# Standard Library
from unittest import mock

# Sematic
from sematic.resolvers.cloud_resolver import CloudResolver
from sematic.resolvers.worker import main
from sematic.calculator import func
from sematic.api.tests.fixtures import (  # noqa: F401
    mock_no_auth,
    mock_requests,
    test_client,
)
from sematic.db.tests.fixtures import test_db  # noqa: F401
from sematic.tests.fixtures import test_storage  # noqa: F401
from sematic.db.queries import get_root_graph


@func
def add(a: float, b: float) -> float:
    return a + b


# TODO: support pipeline args
@func
def pipeline(a: float, b: float) -> float:
    return add(a, b)


@mock.patch("sematic.resolvers.cloud_resolver._schedule_job")
@mock.patch("kubernetes.config.load_kube_config")
@mock_no_auth
def test_main(
    mock_load_kube_config: mock.MagicMock,
    mock_schedule_job: mock.MagicMock,
    mock_requests,  # noqa: F811
    test_db,  # noqa: F811
    test_storage,  # noqa: F811
):
    # On the user's machine
    resolver = CloudResolver(detach=True)

    future = pipeline(1, 2)

    future.resolve(resolver)

    # In the driver job

    main(run_id=future.id, resolve=True)

    runs, artifacts, edges = get_root_graph(future.id)
    assert len(runs) == 2
    assert len(artifacts) == 3
    assert len(edges) == 6
