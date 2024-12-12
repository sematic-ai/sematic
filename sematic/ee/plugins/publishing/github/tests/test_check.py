# Standard Library
from dataclasses import dataclass
from typing import Dict, List
from unittest.mock import MagicMock, patch

# Third-party
import pytest

# Sematic
from sematic.abstract_future import FutureState
from sematic.db.models.git_info import GitInfo
from sematic.db.models.resolution import Resolution
from sematic.db.models.run import Run
from sematic.db.queries import save_resolution, save_run
from sematic.db.tests.fixtures import (  # noqa: F401
    allow_any_run_state_transition,
    make_resolution,
    make_run,
    run,
    test_db,
)
from sematic.ee.plugins.publishing.github.check import (
    State,
    _get_runs,
    _validate_run_git_info,
    check_commit,
    check_runs,
)


@dataclass
class Fixture:
    runs_by_commit_sha: Dict[str, List[Run]]
    resolutions_by_commit_sha: Dict[str, List[Resolution]]
    git_info_by_commit_sha: Dict[str, GitInfo]
    requests_mock: MagicMock
    target_url_mock: MagicMock

    def commit_shas(self):
        return list(self.git_info_by_commit_sha.keys())

    def git_infos(self):
        return list(self.git_info_by_commit_sha.values())


@pytest.fixture
def commit_check_environment(test_db, allow_any_run_state_transition):  # noqa: F811
    commit_sha_1 = 40 * "1"
    commit_sha_2 = 40 * "2"

    git_info_1 = GitInfo(
        remote="https://github.com/acme/anvil.git",
        branch="main",
        commit=commit_sha_1,
        dirty=False,
    )
    git_info_2 = GitInfo(
        remote="git@github.com:corneria/fox.git",
        branch="main",
        commit=commit_sha_2,
        dirty=False,
    )
    resolution_1a = make_resolution(git_info=git_info_1, root_id=16 * "1a")
    resolution_1b = make_resolution(git_info=git_info_1, root_id=16 * "1b")
    resolution_2a = make_resolution(git_info=git_info_2, root_id=16 * "2a")
    resolution_2b = make_resolution(git_info=git_info_2, root_id=16 * "2b")
    run_1a = make_run(
        id=resolution_1a.root_id,
        root_id=resolution_1a.root_id,
        tags=[f"checks-commit:{commit_sha_1}"],
        future_state=FutureState.SCHEDULED,
    )
    run_1b = make_run(
        id=resolution_1b.root_id,
        root_id=resolution_1b.root_id,
        tags=[f"checks-commit:{commit_sha_1}"],
        future_state=FutureState.SCHEDULED,
    )
    run_2a = make_run(
        id=resolution_2a.root_id,
        root_id=resolution_2a.root_id,
        tags=[f"checks-commit:{commit_sha_2}"],
        future_state=FutureState.SCHEDULED,
    )
    run_2b = make_run(
        id=resolution_2b.root_id,
        root_id=resolution_2b.root_id,
        tags=[f"checks-commit:{commit_sha_2}"],
        future_state=FutureState.SCHEDULED,
    )

    for run in [run_1a, run_1b, run_2a, run_2b]:  # noqa: F402
        save_run(run)

    for resolution in [resolution_1a, resolution_1b, resolution_2a, resolution_2b]:
        save_resolution(resolution)

    with (
        patch("sematic.ee.plugins.publishing.github.check.requests") as mock_requests,
        patch(
            "sematic.ee.plugins.publishing.github.check.get_access_token"
        ) as mock_get_access_token,
        patch(
            "sematic.ee.plugins.publishing.github.check._details_url"
        ) as mock_details_url,
    ):
        mock_get_access_token.return_value = "fake-token"
        mock_details_url.side_effect = lambda sha: f"http://sematic.test/{sha}"

        yield Fixture(
            runs_by_commit_sha={
                commit_sha_1: [run_1a, run_1b],
                commit_sha_2: [run_2a, run_2b],
            },
            resolutions_by_commit_sha={
                commit_sha_1: [
                    resolution_1a,
                    resolution_1b,
                ],
                commit_sha_2: [
                    resolution_2a,
                    resolution_2b,
                ],
            },
            git_info_by_commit_sha={
                commit_sha_1: git_info_1,
                commit_sha_2: git_info_2,
            },
            requests_mock=mock_requests,
            target_url_mock=mock_details_url,
        )


def test_check_commit(commit_check_environment):
    info_1, info_2 = commit_check_environment.git_infos()
    info_2.dirty = True
    resolution_2a = commit_check_environment.resolutions_by_commit_sha[info_2.commit][0]
    resolution_2a.git_info = info_2
    save_resolution(resolution_2a)

    check_result = check_commit(info_1)
    assert check_result is not None
    assert check_result.state == State.pending.value
    commit_check_environment.requests_mock.post.assert_called_once()
    commit_check_environment.requests_mock.reset_mock()

    check_result = check_commit(info_2)
    assert check_result is not None
    assert check_result.state == State.error.value
    commit_check_environment.requests_mock.post.assert_called_once()


def test_get_runs(commit_check_environment):
    for commit_sha, runs in commit_check_environment.runs_by_commit_sha.items():
        actual_runs = _get_runs(commit_sha)
        assert {r.id for r in runs} == {r.id for r in actual_runs}


def test_validate_run_git_info(commit_check_environment):
    extra_run_1 = make_run(id=32 * "e", root_id=32 * "e")
    extra_run_2 = make_run(id=32 * "f", root_id=extra_run_1.id)
    save_run(extra_run_1)
    save_run(extra_run_2)
    git_info = commit_check_environment.git_infos()[0]
    target_url = commit_check_environment.target_url_mock(git_info.commit)
    check_result = _validate_run_git_info([extra_run_2], git_info, target_url)
    assert check_result is not None
    assert check_result.state == State.error.value
    assert check_result.description == (
        "Run ffffffffffffffffffffffffffffffff is not the root run of a pipeline."
    )

    info_1, info_2 = commit_check_environment.git_infos()
    info_2.dirty = True
    resolution_2a = commit_check_environment.resolutions_by_commit_sha[info_2.commit][0]
    resolution_2a.git_info = info_2
    save_resolution(resolution_2a)

    check_result = _validate_run_git_info(
        commit_check_environment.runs_by_commit_sha[info_2.commit], info_2, target_url
    )
    assert check_result is not None
    assert check_result.state == State.error.value
    assert check_result.description == (
        "Run 2a2a2a2a2a2a2a2a2a2a2a2a2a2a2a2a was generated from "
        "code with uncommitted changes"
    )

    check_result = _validate_run_git_info(
        commit_check_environment.runs_by_commit_sha[info_1.commit], info_2, target_url
    )
    assert check_result is not None
    assert check_result.state == State.error.value
    assert check_result.description == (
        "Run 1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a isn't using code "
        "for commit 2222222222222222222222222222222222222222"
    )

    resolution_2a.git_info = None
    save_resolution(resolution_2a)
    check_result = _validate_run_git_info(
        commit_check_environment.runs_by_commit_sha[info_2.commit], info_2, target_url
    )
    assert check_result is not None
    assert check_result.state == State.error.value
    assert check_result.description == (
        "Run 2a2a2a2a2a2a2a2a2a2a2a2a2a2a2a2a doesn't have Git info."
    )

    check_result = _validate_run_git_info(
        commit_check_environment.runs_by_commit_sha[info_1.commit], info_1, target_url
    )
    assert check_result is None


CHECK_RUNS_CASES = [
    ([], State.success, "All 0 runs have succeeded."),
    (
        [make_run(future_state=FutureState.CREATED.value)],
        State.pending,
        "Completed 0 runs of 1.",
    ),
    (
        [make_run(future_state=FutureState.RAN.value)],
        State.pending,
        "Completed 0 runs of 1.",
    ),
    (
        [make_run(future_state=FutureState.RESOLVED.value)],
        State.success,
        "All 1 runs have succeeded.",
    ),
    (
        [make_run(future_state=FutureState.CANCELED.value, id=32 * "1")],
        State.failure,
        "Run 11111111111111111111111111111111 for 'path.to.test_run' did not succeed.",
    ),
    (
        [make_run(future_state=FutureState.FAILED.value, id=32 * "1")],
        State.failure,
        "Run 11111111111111111111111111111111 for 'path.to.test_run' did not succeed.",
    ),
    (
        [make_run(future_state=FutureState.NESTED_FAILED.value, id=32 * "1")],
        State.failure,
        "Run 11111111111111111111111111111111 for 'path.to.test_run' did not succeed.",
    ),
    (
        [
            make_run(future_state=FutureState.SCHEDULED.value, id=32 * "1"),
            make_run(future_state=FutureState.RAN.value, id=32 * "2"),
        ],
        State.pending,
        "Completed 0 runs of 2.",
    ),
    (
        [
            make_run(future_state=FutureState.SCHEDULED.value, id=32 * "1"),
            make_run(future_state=FutureState.RESOLVED.value, id=32 * "2"),
        ],
        State.pending,
        "Completed 1 runs of 2.",
    ),
    (
        [
            make_run(future_state=FutureState.SCHEDULED.value, id=32 * "1"),
            make_run(future_state=FutureState.FAILED.value, id=32 * "2"),
        ],
        State.failure,
        "Run 22222222222222222222222222222222 for 'path.to.test_run' did not succeed.",
    ),
    (
        [
            make_run(future_state=FutureState.RESOLVED.value, id=32 * "1"),
            make_run(future_state=FutureState.RESOLVED.value, id=32 * "2"),
        ],
        State.success,
        "All 2 runs have succeeded.",
    ),
]


@pytest.mark.parametrize(
    "runs, expected_state, expected_description",
    CHECK_RUNS_CASES,
)
def test_check_runs(runs, expected_state, expected_description):
    fake_url = "http://localhost:5001/fake/url"
    result = check_runs(runs, fake_url)
    assert result is not None
    assert result.target_url == fake_url
    assert result.state == expected_state.value
    assert result.description == expected_description
