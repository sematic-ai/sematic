"""
Module holding common DB queries.
"""
# Glow
from glow.db.models.run import Run
from glow.db.db import db


def count_runs() -> int:
    """
    Counts all runs.

    Returns
    -------
    int
        Run count
    """
    with db().get_session() as session:
        run_count = session.query(Run).count()

    return run_count


def create_run(run: Run) -> Run:
    """
    Create a new run.

    Returns
    -------
    Run
        The newly created run.
    """
    with db().get_session() as session:
        session.add(run)
        session.commit()
        session.refresh(run)

    return run
