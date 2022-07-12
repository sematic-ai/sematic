# Standard Library
from unittest import mock

# Sematic
from sematic.calculator import func
from sematic.resolvers.cloud_resolver import CloudResolver
from sematic.api.tests.fixtures import mock_requests, test_client  # noqa: F401
from sematic.db.tests.fixtures import test_db  # noqa: F401
from sematic.tests.fixtures import test_storage  # noqa: F401
import sematic.api_client as api_client


@func
def add(a: float, b: float) -> float:
    return a + b


# TODO: support pipeline args
@func
def pipeline() -> float:
    return add(1, 2)


@mock.patch("sematic.resolvers.cloud_resolver._schedule_job")
def test_simulate_cloud_exec(
    mock_schedule_job: mock.MagicMock,
    mock_requests,  # noqa: F811
    test_db,  # noqa: F811
    test_storage,  # noqa: F811
):
    # On the user's machine

    resolver = CloudResolver(attach=False)

    future = pipeline()

    result = future.resolve(resolver)

    assert result == future.id

    mock_schedule_job.assert_called_once_with(
        future.id, "sematic-driver-pipeline-{}".format(future.id)
    )

    # In the driver job

    runs, artifacts, edges = api_client.get_graph(future.id)

    driver_resolver = CloudResolver(attach=True)

    driver_resolver.set_graph(runs=runs, artifacts=artifacts, edges=edges)

    output = driver_resolver.resolve(future)

    assert output == 3
