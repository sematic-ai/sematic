# Standard Library
import logging
from dataclasses import dataclass
from enum import Enum, unique
from typing import List, Literal, Optional
from urllib.parse import urlencode

# Sematic
from sematic.abstract_future import FutureState
from sematic.abstract_plugin import AbstractPluginSettingsVar
from sematic.config.server_settings import ServerSettingsVar, get_server_setting

# from sematic.config.settings import get_plugin_setting
from sematic.db.db import db
from sematic.db.models.mixins.json_encodable_mixin import CONTAIN_FILTER_KEY
from sematic.db.models.run import Run

logger = logging.getLogger(__name__)


COMMIT_CHECK_PREFIX = "checks-commit:"


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


def check_commit(commit_sha: str) -> CheckResult:
    runs = _get_runs(commit_sha)
    target_url = _details_url(commit_sha)
    check_result = _validate_run_git_info(runs, commit_sha)
    if check_result is None:
        check_result = check_runs(runs, target_url)
    _update_github(commit_sha, check_result)
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
        (1 for run in runs if FutureState[run.future_state].is_terminal()), 0  # type: ignore
    )
    if n_complete == len(runs):
        return CheckResult(
            state=State.success.value,
            description=f"All {len(runs)} runs have succeeded",
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
            session.query(Run)
            .filter(Run.tags.info[CONTAIN_FILTER_KEY](Run.tags, tag))
            .all()
        )
    return runs


def _details_url(commit_sha: str) -> str:
    tag = f"{COMMIT_CHECK_PREFIX}{commit_sha}"
    base_external_url = get_server_setting(ServerSettingsVar.SEMATIC_DASHBOARD_URL)
    # TODO: Update once this is implemented:
    # https://github.com/sematic-ai/sematic/issues/835
    return f"{base_external_url}/runs?{urlencode(dict(search=tag))}"


def _validate_run_git_info(runs, commit_sha) -> Optional[CheckResult]:
    # TODO: verify all runs are associated with clean git commits on the given sha.
    return None


def _update_github(commit_sha: str, check_result: CheckResult) -> None:
    logger.warning("Not imoplemented! %s", check_result)
