# Standard Library
import re

import pytest

# Sematic
from sematic.db.models.resolution import (
    InvalidResolution,
    Resolution,
    ResolutionKind,
    ResolutionStatus,
)
from sematic.utils.git import GitInfo


def test_is_allowed_transition():
    assert ResolutionStatus.is_allowed_transition(
        ResolutionStatus.SCHEDULED, ResolutionStatus.RUNNING
    )
    assert ResolutionStatus.is_allowed_transition(
        ResolutionStatus.RUNNING, ResolutionStatus.COMPLETE
    )
    assert not ResolutionStatus.is_allowed_transition(
        ResolutionStatus.COMPLETE, ResolutionStatus.FAILED
    )


UPDATE_CASES = [
    (
        Resolution(
            root_id="abc123",
            status=ResolutionStatus.SCHEDULED,
            kind=ResolutionKind.KUBERNETES,
            docker_image_uri="my.docker.registry.io/image/tag",
            git_info=GitInfo(remote="remote", branch="branch", commit="commit", dirty=False),
        ),
        None,
    ),
    (
        Resolution(
            root_id="abc123",
            status=ResolutionStatus.RUNNING,
            kind=ResolutionKind.KUBERNETES,
            docker_image_uri="my.docker.registry.io/image/tag",
            git_info=GitInfo(remote="remote", branch="branch", commit="commit", dirty=False),
        ),
        None,
    ),
    (
        Resolution(
            root_id="zzz",
            status=ResolutionStatus.SCHEDULED,
            kind=ResolutionKind.KUBERNETES,
            docker_image_uri="my.docker.registry.io/image/tag",
            git_info=GitInfo(remote="remote", branch="branch", commit="commit", dirty=False),
        ),
        r"Cannot update root_id of resolution abc123 after it has been created.*zzz.*",
    ),
    (
        Resolution(
            root_id="abc123",
            status=ResolutionStatus.COMPLETE,
            kind=ResolutionKind.KUBERNETES,
            docker_image_uri="my.docker.registry.io/image/tag",
            git_info=GitInfo(remote="remote", branch="branch", commit="commit", dirty=False),
        ),
        r"Resolution abc123 cannot be moved from the SCHEDULED state to the "
        r"COMPLETE state.",
    ),
    (
        Resolution(
            root_id="abc123",
            status=ResolutionStatus.SCHEDULED,
            kind=ResolutionKind.LOCAL,
            docker_image_uri="my.docker.registry.io/image/tag",
            git_info=GitInfo(remote="remote", branch="branch", commit="commit", dirty=False),
        ),
        r"Cannot update kind of resolution abc123 after it has been created.*LOCAL.*",
    ),
    (
        Resolution(
            root_id="abc123",
            status=ResolutionStatus.SCHEDULED,
            kind=ResolutionKind.KUBERNETES,
            docker_image_uri="my.docker.registry.io/changed/tag",
            git_info=GitInfo(remote="remote", branch="branch", commit="commit", dirty=False),
        ),
        r"Cannot update docker_image_uri of resolution abc123 .*changed/tag.*",
    ),
    (
        Resolution(
            root_id="abc123",
            status=ResolutionStatus.SCHEDULED,
            kind=ResolutionKind.KUBERNETES,
            docker_image_uri="my.docker.registry.io/image/tag",
            git_info=GitInfo(remote="remote", branch="branch", commit="commit", dirty=True),
        ),
        r"Cannot update git_info_json of resolution abc123 .*\"dirty\": false.*",
    ),
]


@pytest.mark.parametrize("update,expected_error", UPDATE_CASES)
def test_updates(update, expected_error):
    original = Resolution(
        root_id="abc123",
        status=ResolutionStatus.SCHEDULED,
        kind=ResolutionKind.KUBERNETES,
        docker_image_uri="my.docker.registry.io/image/tag",
        git_info=GitInfo(remote="remote", branch="branch", commit="commit", dirty=False),
    )
    try:
        original.update_with(update)
        error = None
    except InvalidResolution as e:
        error = str(e)
    if expected_error is None:
        assert error is None
    else:
        assert re.match(
            expected_error, error
        ), f"Error: '{error}' didn't match pattern: '{expected_error}'"
