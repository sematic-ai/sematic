"""
Module holding common DB queries.
"""
# Standard library
from typing import List, Set, Tuple

# Third-party
import sqlalchemy
import sqlalchemy.orm

# Sematic
from sematic.db.models.artifact import Artifact
from sematic.db.models.edge import Edge
from sematic.db.models.run import Run
from sematic.db.models.note import Note
from sematic.db.db import db


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


def save_graph(runs: List[Run], artifacts: List[Artifact], edges: List[Edge]):
    """
    Update a graph
    """
    with db().get_session() as session:
        for run in runs:
            session.merge(run)

        for artifact in artifacts:
            session.merge(artifact)

        for edge in edges:
            session.merge(edge)

        session.commit()


def get_graph(root_id: str) -> Tuple[List[Run], List[Artifact], List[Edge]]:
    """
    Retrieve the entire graph for a given root run ID.
    """
    with db().get_session() as session:
        runs: List[Run] = session.query(Run).filter(Run.root_id == root_id).all()
        run_ids = [run.id for run in runs]
        edges: List[Edge] = (
            session.query(Edge)
            .filter(
                sqlalchemy.or_(
                    Edge.source_run_id.in_(run_ids),
                    Edge.destination_run_id.in_(run_ids),
                )
            )
            .all()
        )
        artifact_ids = {edge.artifact_id for edge in edges}
        artifacts: List[Artifact] = (
            session.query(Artifact).filter(Artifact.id.in_(artifact_ids)).all()
        )

    return runs, artifacts, edges


def get_note(note_id: str) -> Note:
    """
    Get note from DB.
    """
    with db().get_session() as session:
        return session.query(Note).filter(Note.id == note_id).one()


def save_note(note: Note) -> Note:
    """
    Persist a note.
    """
    with db().get_session() as session:
        session.add(note)
        session.commit()
        session.refresh(note)

    return note


def delete_note(note: Note):
    """
    Delete note.
    """
    with db().get_session() as session:
        session.delete(note)
        session.commit()


def get_root_graph(root_run_id: str) -> Tuple[Set[Run], Set[Edge], Set[Artifact]]:
    with db().get_session() as session:
        results = (
            session.query(Run, Edge, Artifact)
            .filter(
                sqlalchemy.and_(
                    Run.root_id == root_run_id,
                    sqlalchemy.or_(
                        Edge.source_run_id == Run.id, Edge.destination_run_id == Run.id
                    ),
                    sqlalchemy.or_(
                        Edge.artifact_id == Artifact.id, Edge.artifact_id.is_(None)
                    ),
                )
            )
            .all()
        )

    runs: List[Run] = []
    artifacts: List[Artifact] = []
    edges: List[Edge] = []

    for result in results:
        runs.append(result[0])
        edges.append(result[1])
        artifacts.append(result[2])

    return set(runs), set(edges), set(artifacts)
