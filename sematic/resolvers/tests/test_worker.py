# Standard Library
from unittest import mock

# Sematic
from sematic.resolvers.cloud_resolver import CloudResolver
from sematic.resolvers.worker import main
from sematic.calculator import func
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
def test_main(
    mock_schedule_job: mock.MagicMock,
    mock_requests,  # noqa: F811
    test_db,  # noqa: F811
    test_storage,  # noqa: F811
):
    # On the user's machine
    resolver = CloudResolver(detach=True)

    future = pipeline()

    future.resolve(resolver)

    # In the driver job

    main(run_id=future.id, resolve=True)

    runs, artifacts, edges = api_client.get_graph(future.id)
    assert len(runs) == 2
    assert len(artifacts) == 3
    assert len(edges) == 4
