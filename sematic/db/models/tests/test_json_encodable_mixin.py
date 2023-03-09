# Sematic
from sematic.db.models.run import Run
from sematic.db.tests.fixtures import (  # noqa: F401
    allow_any_run_state_transition,
    persisted_run,
    run,
    test_db,
)


def test_utc_timestamp(persisted_run: Run):  # noqa: F811
    """
    Test that the JSON mixin outputs UTC times even if the DB does not
    store it.
    """
    created_at = persisted_run.to_json_encodable()["created_at"]
    assert created_at == "{}+00:00".format(persisted_run.created_at.isoformat())
