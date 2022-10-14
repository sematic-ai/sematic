# Standard Library
from unittest import mock

# Third-party
import pytest

# Sematic
import sematic.api_client as api_client
from sematic.api.tests.fixtures import (  # noqa: F401
    mock_no_auth,
    mock_requests,
    test_client,
)
from sematic.calculator import func
from sematic.db.models.resolution import ResolutionStatus
from sematic.db.tests.fixtures import test_db  # noqa: F401
from sematic.resolvers.cloud_resolver import CloudResolver
from sematic.tests.fixtures import test_storage, valid_client_version  # noqa: F401


@func(base_image_tag="cuda", inline=False)
def add(a: float, b: float) -> float:
    return a + b


# TODO: support pipeline args
@func
def pipeline() -> float:
    return add(1, 2)


@mock.patch("socketio.Client.connect")
@mock.patch(
    "sematic.resolvers.cloud_resolver.get_image_uris",
    return_value={"default": "foo", "cuda": "bar"},
)
@mock.patch("sematic.api_client.schedule_resolution")
@mock.patch("kubernetes.config.load_kube_config")
@mock.patch("sematic.scheduling.job_scheduler.k8s.schedule_run_job")
@mock_no_auth
def test_simulate_cloud_exec(
    mock_k8s_schedule_run_job: mock.MagicMock,
    mock_load_kube_config: mock.MagicMock,
    mock_schedule_job: mock.MagicMock,
    mock_socketio,
    mock_requests,  # noqa: F811
    test_db,  # noqa: F811
    test_storage,  # noqa: F811
    valid_client_version,  # noqa: F811
):
    # On the user's machine:
    resolver = CloudResolver(detach=True)
    future = pipeline()
    result = future.resolve(resolver)

    assert result == future.id
    mock_schedule_job.assert_called_once_with(future.id)
    resolution = api_client.get_resolution(future.id)
    assert resolution.status == ResolutionStatus.CREATED.value
    assert resolution.container_image_uris == {"default": "foo", "cuda": "bar"}
    resolution.status = ResolutionStatus.SCHEDULED
    api_client.save_resolution(resolution)

    # In the driver job:
    runs, artifacts, edges = api_client.get_graph(future.id)

    root_run = next(run for run in runs if run.id == future.id)
    assert root_run.container_image_uri == "foo"
    add_run = next(run for run in runs if run.id != future.id)
    assert add_run.container_image_uri == "bar"

    driver_resolver = CloudResolver(detach=False, is_running_remotely=True)
    driver_resolver.set_graph(runs=runs, artifacts=artifacts, edges=edges)
    assert (
        api_client.get_resolution(future.id).status == ResolutionStatus.SCHEDULED.value
    )
    output = driver_resolver.resolve(future)

    assert output == 3
    assert (
        api_client.get_resolution(future.id).status == ResolutionStatus.COMPLETE.value
    )

    mock_k8s_schedule_run_job.assert_called_once_with(
        run_id=add_run.id,
        image="bar",
        user_settings={},
        resource_requirements=None,
        try_number=0,
    )

    # cheap way of confirming no k8s calls were made
    mock_load_kube_config.assert_not_called()


@pytest.mark.parametrize(
    "max_parallelism, expected_validates",
    (
        (None, True),
        (0, False),
        (-1, False),
        (1, True),
        (10, True),
    ),
)
def test_max_parallelism_validation(max_parallelism, expected_validates):
    try:
        CloudResolver(max_parallelism=max_parallelism)
    except ValueError:
        assert not expected_validates
        return
    assert expected_validates
