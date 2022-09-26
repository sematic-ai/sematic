# Standard Library
from unittest import mock

import pytest

# Sematic
from sematic.abstract_future import FutureState
from sematic.api.tests.fixtures import (  # noqa: F401
    mock_no_auth,
    mock_requests,
    test_client,
)
from sematic.calculator import func
from sematic.db.models.resolution import ResolutionStatus
from sematic.db.queries import get_resolution, get_root_graph, save_resolution
from sematic.db.tests.fixtures import test_db  # noqa: F401
from sematic.resolvers.cloud_resolver import CloudResolver
from sematic.resolvers.worker import main
from sematic.tests.fixtures import test_storage, valid_client_version  # noqa: F401


@func
def add(a: float, b: float) -> float:
    return a + b


@func
def pipeline(a: float, b: float) -> float:
    return add(a, b)


@mock.patch("sematic.resolvers.cloud_resolver.get_image_uri")
@mock.patch("sematic.api_client.schedule_resolution")
@mock.patch("kubernetes.config.load_kube_config")
@mock_no_auth
def test_main(
    mock_load_kube_config: mock.MagicMock,
    mock_schedule_job: mock.MagicMock,
    mock_get_image: mock.MagicMock,
    mock_requests,  # noqa: F811
    test_db,  # noqa: F811
    test_storage,  # noqa: F811
    valid_client_version,  # noqa: F811
):
    mock_get_image.return_value = "some_image"

    # On the user's machine
    resolver = CloudResolver(detach=True)

    future = pipeline(1, 2)

    future.resolve(resolver)
    resolution = get_resolution(future.id)
    resolution.status = ResolutionStatus.SCHEDULED
    save_resolution(resolution)

    # In the driver job

    main(run_id=future.id, resolve=True)

    runs, artifacts, edges = get_root_graph(future.id)
    assert len(runs) == 2
    assert len(artifacts) == 3
    assert len(edges) == 6


@func
def fail():
    raise Exception("FAIL!")


@mock.patch("sematic.resolvers.cloud_resolver.get_image_uri")
@mock.patch("sematic.api_client.schedule_resolution")
@mock.patch("kubernetes.config.load_kube_config")
@mock_no_auth
def test_fail(
    mock_load_kube_config: mock.MagicMock,
    mock_schedule_job: mock.MagicMock,
    mock_get_image: mock.MagicMock,
    mock_requests,  # noqa: F811
    test_storage,  # noqa: F811
    valid_client_version,  # noqa: F811
):
    mock_get_image.return_value = "some_image"

    # On the user's machine
    resolver = CloudResolver(detach=True)

    future = fail()

    future.resolve(resolver)
    resolution = get_resolution(future.id)
    resolution.status = ResolutionStatus.SCHEDULED
    save_resolution(resolution)

    # In the driver job
    with pytest.raises(Exception, match="FAIL!"):
        main(run_id=future.id, resolve=True)

    runs, _, _ = get_root_graph(future.id)

    assert runs[0].future_state == FutureState.FAILED.value
    assert runs[0].exception is not None
    assert "FAIL!" in runs[0].exception.repr
