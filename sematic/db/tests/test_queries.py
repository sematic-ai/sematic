# Third-party
import pytest

# Sematic
from sematic.api.tests.fixtures import (  # noqa: F401
    mock_auth,
    mock_requests,
    mock_socketio,
    test_client,
)
from sematic.calculator import func
from sematic.db.models.artifact import Artifact
from sematic.db.models.factories import make_artifact
from sematic.db.models.resolution import Resolution, ResolutionStatus
from sematic.db.models.run import Run
from sematic.db.queries import (
    count_runs,
    get_artifact,
    get_resolution,
    get_root_graph,
    get_run,
    get_run_graph,
    save_graph,
    save_resolution,
    save_run,
)
from sematic.db.tests.fixtures import (  # noqa: F401
    make_run,
    persisted_artifact,
    persisted_resolution,
    persisted_run,
    pg_mock,
    run,
    test_db,
)
from sematic.resolvers.tests.fixtures import mock_local_resolver_storage  # noqa: F401
from sematic.tests.fixtures import test_storage, valid_client_version  # noqa: F401


def test_count_runs(test_db, run: Run):  # noqa: F811
    assert count_runs() == 0
    save_run(run)
    assert count_runs() == 1


def test_create_run(test_db, run: Run):  # noqa: F811
    assert run.created_at is None
    created_run = save_run(run)
    assert created_run == run
    assert run.created_at is not None
    assert run.updated_at is not None


def test_get_run(test_db, persisted_run: Run):  # noqa: F811
    fetched_run = get_run(persisted_run.id)

    assert fetched_run.id == persisted_run.id


def test_save_run(test_db, persisted_run: Run):  # noqa: F811
    persisted_run.name = "New Name"
    old_updated_at = persisted_run.updated_at
    save_run(persisted_run)
    fetched_run = get_run(persisted_run.id)
    assert fetched_run.name == "New Name"
    assert fetched_run.updated_at > old_updated_at


def test_get_resolution(test_db, persisted_resolution: Resolution):  # noqa: F811
    fetched_resolution = get_resolution(persisted_resolution.root_id)
    assert fetched_resolution.root_id == persisted_resolution.root_id
    assert fetched_resolution.status == persisted_resolution.status
    assert fetched_resolution.kind == persisted_resolution.kind
    assert (
        fetched_resolution.container_image_uris
        == persisted_resolution.container_image_uris
    )
    assert fetched_resolution.git_info == persisted_resolution.git_info
    assert (
        fetched_resolution.settings_env_vars == persisted_resolution.settings_env_vars
    )


def test_save_resolution(test_db, persisted_resolution: Resolution):  # noqa: F811
    assert persisted_resolution.status != ResolutionStatus.FAILED
    persisted_resolution.status = ResolutionStatus.FAILED
    save_resolution(persisted_resolution)
    fetched_resolution = get_resolution(persisted_resolution.root_id)
    assert fetched_resolution.status == ResolutionStatus.FAILED.value

    # multiple updates should be ok
    persisted_resolution.status = ResolutionStatus.COMPLETE
    save_resolution(persisted_resolution)
    fetched_resolution = get_resolution(persisted_resolution.root_id)
    assert fetched_resolution.status == ResolutionStatus.COMPLETE.value


def test_get_artifact(test_db, persisted_artifact: Artifact):  # noqa: F811
    artifact = get_artifact(persisted_artifact.id)

    assert artifact.id == persisted_artifact.id
    assert artifact.type_serialization == persisted_artifact.type_serialization
    assert artifact.json_summary == artifact.json_summary


def test_save_artifact(test_db, test_storage):  # noqa: F811
    artifact = make_artifact(42, int, storage=test_storage)
    save_graph(artifacts=[artifact], runs=[], edges=[])
    persisted_artifact = get_artifact(artifact.id)  # noqa: F811

    assert persisted_artifact.id == artifact.id
    assert persisted_artifact.type_serialization == artifact.type_serialization
    assert persisted_artifact.json_summary == artifact.json_summary
    assert persisted_artifact.created_at == artifact.created_at
    assert persisted_artifact.updated_at == artifact.updated_at


def test_update_artifact(test_db, test_storage):  # noqa: F811
    original_artifact = make_artifact(42, int, storage=test_storage)
    # create copies of these values, as sqlalchemy updates models in-place
    original_created_at = original_artifact.created_at
    original_updated_at = original_artifact.updated_at
    save_graph(artifacts=[original_artifact], runs=[], edges=[])

    updated_artifact = make_artifact(42, int, storage=test_storage)
    assert updated_artifact.created_at != original_created_at

    save_graph(artifacts=[updated_artifact], runs=[], edges=[])

    persisted_artifact = get_artifact(original_artifact.id)  # noqa: F811

    assert persisted_artifact.id == original_artifact.id
    assert persisted_artifact.type_serialization == original_artifact.type_serialization
    assert persisted_artifact.json_summary == original_artifact.json_summary

    assert persisted_artifact.created_at == original_created_at
    assert persisted_artifact.updated_at == original_updated_at


def test_update_artifact_changed_content(test_db, test_storage):  # noqa: F811
    original_artifact = make_artifact(42, int, storage=test_storage)
    # create copies of these values, as sqlalchemy updates models in-place
    original_created_at = original_artifact.created_at
    original_updated_at = original_artifact.updated_at
    save_graph(artifacts=[original_artifact], runs=[], edges=[])

    updated_artifact = make_artifact(42, int, storage=test_storage)

    # json of " 42" still deserializes to 42, but this change
    # helps us validate immutability
    updated_artifact.json_summary = f" {updated_artifact.json_summary}"

    with pytest.raises(
        ValueError, match="Artifact content change detected for field 'json_summary'"
    ):
        save_graph(artifacts=[updated_artifact], runs=[], edges=[])

    persisted_artifact = get_artifact(original_artifact.id)  # noqa: F811

    assert persisted_artifact.id == original_artifact.id
    assert persisted_artifact.type_serialization == original_artifact.type_serialization
    assert persisted_artifact.json_summary == original_artifact.json_summary

    assert persisted_artifact.created_at == original_created_at
    assert persisted_artifact.updated_at == original_updated_at


@func
def add(a: float, b: float) -> float:
    return a + b


@func
def pipeline(a: float, b: float) -> float:
    return add(add(a, b), b)


@pytest.mark.parametrize(
    "fn, run_count, artifact_count, edge_count",
    ((get_run_graph, 1, 3, 3), (get_root_graph, 3, 4, 8)),
)
def test_get_run_graph(
    mock_auth,  # noqa: F811
    mock_local_resolver_storage,  # noqa: F811
    mock_socketio,  # noqa: F811
    fn,
    run_count: int,
    artifact_count: int,
    edge_count: int,
    mock_requests,  # noqa: F811
    valid_client_version,  # noqa: F811
):

    future = pipeline(1, 2)
    future.resolve()

    runs, artifacts, edges = fn(future.id)

    assert len(runs) == run_count
    assert len(artifacts) == artifact_count
    assert len(edges) == edge_count
