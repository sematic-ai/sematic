# Standard Library
import uuid

# Glow
from glow.abstract_future import FutureState
from glow.db.models.run import Run
from glow.db.db import db
from glow.db.queries import count_runs, create_run
from glow.db.tests.fixtures import test_db  # noqa: F401


def test_db_fixture(test_db):  # noqa: F811
    assert count_runs() == 0

    run = Run(
        id=uuid.uuid4().hex,
        future_state=FutureState.CREATED,
        name="test_run",
        calculator_path="path.to.test_run",
    )

    create_run(run)

    assert count_runs() == 1

    assert run.created_at is not None
    assert run.updated_at is not None


def test_test_db_engine(test_db):  # noqa: F811
    engine = db().get_engine()
    assert str(engine.url) == "sqlite://"
