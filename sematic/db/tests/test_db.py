# Sematic
from sematic.db.models.run import Run
from sematic.db.queries import count_runs, save_run
from sematic.db.tests.fixtures import run, test_db, pg_mock  # noqa: F401


def test_db_fixture(test_db, run: Run):  # noqa: F811
    assert count_runs() == 0

    save_run(run)

    assert count_runs() == 1

    assert run.created_at is not None
    assert run.updated_at is not None
