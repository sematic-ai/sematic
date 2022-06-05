# Standard library
import typing

# Glow
from glow.db.db import db
from glow.db.models.edge import Edge
from glow.db.queries import (
    count_runs,
    get_run,
    get_run_input_artifacts,
    get_run_output_artifact,
    save_run,
    create_run_with_artifacts,
    set_run_output_artifact,
)
from glow.db.models.artifact import Artifact
from glow.db.models.factories import make_artifact
from glow.db.models.run import Run
from glow.db.tests.fixtures import (  # noqa: F401
    make_run,
    test_db,
    pg_mock,
    run,
    persisted_run,
)


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


def test_create_run_with_artifacts(test_db):  # noqa: F811
    artifacts = dict(a=make_artifact(1, int), b=make_artifact(2, int))

    # Creating two runs with the same artifacts to test artifact
    # deduplication
    for run in [make_run(), make_run()]:  # noqa: F402
        created_run = create_run_with_artifacts(run, artifacts)

        assert created_run.id == run.id
        assert created_run.created_at is not None
        assert created_run.updated_at is not None

        assert get_run(run.id).id == run.id

        with db().get_session() as session:
            edges: typing.List[Edge] = (
                session.query(Edge).filter(Edge.destination_run_id == run.id).all()
            )

        edges_by_name = {edge.destination_name: edge for edge in edges}

        assert set(edges_by_name.keys()) == {"a", "b"}

        for name, artifact in artifacts.items():
            assert artifact.created_at is not None
            assert artifact.updated_at is not None
            assert edges_by_name[name].artifact_id == artifact.id

    # Count total number of artifact created
    with db().get_session() as session:
        assert session.query(Artifact).count() == 2


def test_get_run_input_artifacts(test_db, run: Run):  # noqa: F811
    artifacts = dict(a=make_artifact(1, int), b=make_artifact(2, int))

    create_run_with_artifacts(run, artifacts)

    input_artifacts = get_run_input_artifacts(run.id)

    assert set(input_artifacts) == set(artifacts)
    assert input_artifacts["a"].id == artifacts["a"].id
    assert input_artifacts["b"].id == artifacts["b"].id


def test_get_run_output_artifacts(test_db, persisted_run: Run):  # noqa: F811
    artifact = make_artifact(3, int)

    set_run_output_artifact(persisted_run, artifact)

    output_artifact = get_run_output_artifact(persisted_run.id)

    assert output_artifact is not None
    assert output_artifact.id == artifact.id
    assert output_artifact.json_summary == "3"
