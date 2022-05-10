# Glow
from glow.db.queries import count_runs, create_run, get_run, save_run
from glow.db.models.run import Run
from glow.db.tests.fixtures import test_db, run, persisted_run  # noqa: F401


def test_count_runs(test_db, run: Run):  # noqa: F811
    assert count_runs() == 0
    create_run(run)
    assert count_runs() == 1


def test_create_run(test_db, run: Run):  # noqa: F811
    assert run.created_at is None
    created_run = create_run(run)
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
