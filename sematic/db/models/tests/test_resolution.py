# Standard Library
import re

# Third-party
import pytest

# Sematic
from sematic.db.models.git_info import GitInfo
from sematic.db.models.resolution import (
    InvalidResolution,
    ResolutionKind,
    ResolutionStatus,
)
from sematic.db.tests.fixtures import make_resolution


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
        make_resolution(
            root_id="abc123",
            status=ResolutionStatus.SCHEDULED,
            kind=ResolutionKind.KUBERNETES,
            container_image_uri="my.docker.registry.io/image/tag",
            container_image_uris={"default": "my.docker.registry.io/image/tag"},
            git_info=GitInfo(remote="r", branch="b", commit="c", dirty=False),
        ),
        None,
    ),
    (
        make_resolution(
            root_id="abc123",
            status=ResolutionStatus.RUNNING,
            kind=ResolutionKind.KUBERNETES,
            container_image_uri="my.docker.registry.io/image/tag",
            container_image_uris={"default": "my.docker.registry.io/image/tag"},
            git_info=GitInfo(remote="r", branch="b", commit="c", dirty=False),
        ),
        None,
    ),
    (
        make_resolution(
            root_id="zzz",
            status=ResolutionStatus.SCHEDULED,
            kind=ResolutionKind.KUBERNETES,
            container_image_uri="my.docker.registry.io/image/tag",
            container_image_uris={"default": "my.docker.registry.io/image/tag"},
            git_info=GitInfo(remote="r", branch="b", commit="c", dirty=False),
        ),
        r"Cannot update root_id of resolution abc123 after it has been created.*zzz.*",
    ),
    (
        make_resolution(
            root_id="abc123",
            status=ResolutionStatus.COMPLETE,
            kind=ResolutionKind.KUBERNETES,
            container_image_uri="my.docker.registry.io/image/tag",
            container_image_uris={"default": "my.docker.registry.io/image/tag"},
            git_info=GitInfo(remote="r", branch="b", commit="c", dirty=False),
        ),
        r"Resolution abc123 cannot be moved from the SCHEDULED state to the "
        r"COMPLETE state.",
    ),
    (
        make_resolution(
            root_id="abc123",
            status=ResolutionStatus.SCHEDULED,
            kind=ResolutionKind.LOCAL,
            container_image_uri="my.docker.registry.io/image/tag",
            container_image_uris={"default": "my.docker.registry.io/image/tag"},
            git_info=GitInfo(remote="r", branch="b", commit="c", dirty=False),
        ),
        r"Cannot update kind of resolution abc123 after it has been created.*LOCAL.*",
    ),
    (
        make_resolution(
            root_id="abc123",
            status=ResolutionStatus.SCHEDULED,
            kind=ResolutionKind.KUBERNETES,
            container_image_uri="my.docker.registry.io/changed/tag",
            container_image_uris={"my.docker.registry.io/changed/tag"},
            git_info=GitInfo(remote="r", branch="b", commit="c", dirty=False),
        ),
        r"Cannot update container_image_uris of resolution abc123 .*changed/tag.*",
    ),
    (
        make_resolution(
            root_id="abc123",
            status=ResolutionStatus.SCHEDULED,
            kind=ResolutionKind.KUBERNETES,
            container_image_uri="my.docker.registry.io/image/tag",
            container_image_uris={"default": "my.docker.registry.io/image/tag"},
            git_info=GitInfo(remote="r", branch="b", commit="c", dirty=True),
        ),
        r"Cannot update git_info_json of resolution abc123 .*\"dirty\": false.*",
    ),
]


@pytest.mark.parametrize("update,expected_error", UPDATE_CASES)
def test_updates(update, expected_error):
    original = make_resolution(
        root_id="abc123",
        status=ResolutionStatus.SCHEDULED,
        kind=ResolutionKind.KUBERNETES,
        container_image_uri="my.docker.registry.io/image/tag",
        container_image_uris={"default": "my.docker.registry.io/image/tag"},
        git_info=GitInfo(remote="r", branch="b", commit="c", dirty=False),
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
