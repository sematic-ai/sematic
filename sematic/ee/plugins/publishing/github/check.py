# Standard Library
import logging
from dataclasses import asdict, dataclass
from enum import Enum, unique
from typing import List, Literal, Optional
from urllib.parse import urlencode

# Third-party
import requests

# Sematic
from sematic.abstract_future import FutureState
from sematic.abstract_plugin import AbstractPluginSettingsVar
from sematic.config.server_settings import ServerSettingsVar, get_server_setting
from sematic.config.settings import get_plugin_setting
from sematic.db.db import db
from sematic.db.models.git_info import GitInfo
from sematic.db.models.mixins.json_encodable_mixin import CONTAIN_FILTER_KEY
from sematic.db.models.resolution import Resolution
from sematic.db.models.run import Run
from sematic.utils.retry import retry

logger = logging.getLogger(__name__)


COMMIT_CHECK_PREFIX = "checks-commit:"
CHECK_NAME = "sematic-pipelines-pass"


class GitHubPublisherSettingsVar(AbstractPluginSettingsVar):
    GITHUB_ACCESS_TOKEN = "GITHUB_ACCESS_TOKEN"


StateStr = Literal["success", "pending", "error", "failure"]


@unique
class State(Enum):
    # See:
    # https://docs.github.com/en/rest/commits/statuses?#create-a-commit-status
    success: StateStr = "success"
    pending: StateStr = "pending"
    error: StateStr = "error"
    failure: StateStr = "failure"


@dataclass(frozen=True)
class CheckResult:
    """Results of a commit check.

    See GitHub documentation for more details; fields here relate to
    the equivalently named fields here:
    https://docs.github.com/en/rest/commits/statuses?apiVersion=2022-11-28#create-a-commit-status
    """

    state: StateStr
    description: str
    target_url: str


def check_commit(git_info: GitInfo) -> CheckResult:
    commit_sha = git_info.commit
    logger.info("Checking git commit %s", commit_sha)
    runs = _get_runs(commit_sha)
    target_url = _details_url(commit_sha)
    check_result = _validate_run_git_info(runs, git_info, target_url)
    if check_result is None:
        check_result = check_runs(runs, target_url)
    _update_github(check_result, git_info)
    return check_result


def check_runs(runs: List[Run], target_url: str) -> CheckResult:
    bad_run = next(
        (
            run
            for run in runs
            if FutureState[run.future_state].is_terminal()  # type: ignore
            and run.future_state != FutureState.RESOLVED.value
        ),
        None,
    )
    if bad_run is not None:
        return CheckResult(
            state=State.failure.value,
            description=(
                f"Run {bad_run.id} for '{bad_run.function_path}' did not succeed."
            ),
            target_url=target_url,
        )
    n_complete = sum(
        (1 for r in runs if FutureState[r.future_state].is_terminal()),  # type: ignore
        0,
    )
    if n_complete == len(runs):
        return CheckResult(
            state=State.success.value,
            description=f"All {len(runs)} runs have succeeded.",
            target_url=target_url,
        )

    return CheckResult(
        state=State.pending.value,
        description=f"Completed {n_complete} runs of {len(runs)}.",
        target_url=target_url,
    )


def _get_runs(commit_sha: str) -> List[Run]:
    tag = f"{COMMIT_CHECK_PREFIX}{commit_sha}"
    with db().get_session() as session:
        runs = list(
            session.query(Run)  # type: ignore
            .filter(Run.tags.info[CONTAIN_FILTER_KEY](Run.tags, tag))
            .all()
        )
    return runs


def _details_url(commit_sha: str) -> str:
    tag = f"{COMMIT_CHECK_PREFIX}{commit_sha}"
    base_external_url = get_server_setting(ServerSettingsVar.SEMATIC_DASHBOARD_URL)
    # TODO: Update once this is implemented:
    # https://github.com/sematic-ai/sematic/issues/835
    return f"{base_external_url}/runs#{urlencode(dict(search=tag))}"


def _validate_run_git_info(
    runs: List[Run], git_info: GitInfo, target_url: str
) -> Optional[CheckResult]:
    non_root_run = next((run for run in runs if run.root_id != run.id), None)
    if non_root_run is not None:
        return CheckResult(
            state=State.error.value,
            description=f"Run {non_root_run.id} is not the root run of a pipeline.",
            target_url=target_url,
        )

    resolution_ids = [run.id for run in runs]
    with db().get_session() as session:
        resolutions = (
            session.query(Resolution)  # type: ignore
            .filter(
                Resolution.root_id.in_(resolution_ids),
            )
            .all()
        )

    error_message = None
    for resolution in resolutions:
        if resolution.git_info is None:
            error_message = f"Run {resolution.root_id} doesn't have Git info."
            break
        run_git_info: GitInfo = resolution.git_info
        if run_git_info.commit != git_info.commit:
            error_message = (
                f"Run {resolution.root_id} isn't "
                f"using code for commit {git_info.commit}"
            )
            break
        if run_git_info.dirty:
            error_message = (
                f"Run {resolution.root_id} was generated "
                f"from code with uncommitted changes"
            )
            break
    if error_message is None:
        return None
    return CheckResult(
        state=State.error.value,
        description=error_message,
        target_url=target_url,
    )


@retry(exceptions=(Exception,), tries=5, delay=3, jitter=1)
def _update_github(check_result: CheckResult, git_info: GitInfo) -> None:
    access_token = get_access_token()
    owner, repo = git_info.remote.split("/")[-2:]
    owner = owner.replace("git@github.com:", "")
    repo = repo.replace(".git", "")
    url = f"https://api.github.com/repos/{owner}/{repo}/statuses/{git_info.commit}"
    response = requests.post(
        url,
        json=dict(
            context=CHECK_NAME,
            **asdict(check_result),
        ),
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {access_token}",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    logger.debug("GitHub commit update response: %s", response.text)
    try:
        response.raise_for_status()
    except Exception as e:
        logger.error(
            "GitHub commit update %s response for %s: %s",
            response.status_code,
            url,
            response.text,
        )
        raise RuntimeError(
            f"Error updating GitHub with check for commit {git_info.commit}"
        ) from e


def get_access_token() -> str:
    # local import to break the dependency cycle
    # publisher -> check -> publisher
    # Sematic
    from sematic.ee.plugins.publishing.github.publisher import GitHubPublisher

    return get_plugin_setting(
        GitHubPublisher,
        GitHubPublisherSettingsVar.GITHUB_ACCESS_TOKEN,
    )
