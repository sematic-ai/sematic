"""
Module holding common DB queries.
"""
# Standard library
import typing

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

    Parameters
    ----------
    run : Run
        Run to persist.

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


def get_run(run_id: str) -> Run:
    """
    Get a run from the database.

    Parameters
    ----------
    run_id : str
        ID of run to retrieve.

    Returns
    -------
    Run
        Fetched run
    """
    with db().get_session() as session:
        return session.query(Run).filter(Run.id == run_id).one()


def save_run(run: Run) -> Run:
    """
    Save run to the database.

    Parameters
    ----------
    run : Run
        Run to save

    Returns
    -------
    Run
        saved run
    """
    with db().get_session() as session:
        session.add(run)
        session.commit()
        session.refresh(run)

    return run


def list_runs() -> typing.List[Run]:
    with db().get_session() as session:
        return session.query(Run).all()
