from glow.calculator import calculator
from glow.db.models.artifact import Artifact
from glow.db.models.edge import Edge
from glow.db.models.factories import make_artifact
from glow.db.models.run import Run
from glow.resolvers.offline_resolver import OfflineResolver
from glow.db.db import db
from glow.db.tests.fixtures import test_db  # noqa: F401


@calculator
def add(a: float, b: float) -> float:
    return a + b


def test_single_calculator(test_db):  # noqa: F811
    future = add(1, 2)

    result = future.set(name="AAA").resolve(OfflineResolver())

    assert result == 3

    with db().get_session() as session:
        runs = session.query(Run).all()
        artifacts = session.query(Artifact).all()
        edges = session.query(Edge).all()

    assert len(runs) == 1
    assert len(artifacts) == 3
    assert len(edges) == 3

    artifact_a = make_artifact(1.0, float)
    artifact_b = make_artifact(2.0, float)
    artifact_output = make_artifact(3.0, float)

    assert set(edges) == {
        Edge(
            source_run_id=None,
            destination_run_id=future.id,
            destination_name="a",
            parent_id=None,
            artifact_id=artifact_a.id,
        ),
        Edge(
            source_run_id=None,
            destination_run_id=future.id,
            destination_name="b",
            parent_id=None,
            artifact_id=artifact_b.id,
        ),
        Edge(
            source_run_id=future.id,
            destination_run_id=None,
            destination_name=None,
            parent_id=None,
            artifact_id=artifact_output.id,
        ),
    }


@calculator
def add_add_add(a: float, b: float) -> float:
    aa = add(a, b)
    bb = add(a, aa)
    return add(bb, aa)


def test_add_add(test_db):  # noqa: F811
    future = add_add_add(1, 2)

    result = future.resolve(OfflineResolver())

    assert result == 7

    with db().get_session() as session:
        runs = session.query(Run).all()
        artifacts = session.query(Artifact).all()
        edges = session.query(Edge).all()

    assert len(runs) == 4
    assert len(artifacts) == 5
    assert len(edges) == 10
