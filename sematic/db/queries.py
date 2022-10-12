"""
Module holding common DB queries.
"""
# Standard Library
import logging
from typing import Dict, List, Set, Tuple

# Third-party
import sqlalchemy
import sqlalchemy.orm
from sqlalchemy.sql.elements import ColumnElement

# Sematic
from sematic.abstract_future import FutureState
from sematic.db.db import db
from sematic.db.models.artifact import Artifact
from sematic.db.models.edge import Edge
from sematic.db.models.note import Note
from sematic.db.models.resolution import Resolution
from sematic.db.models.run import Run
from sematic.db.models.user import User
from sematic.scheduling.external_job import ExternalJob
from sematic.types.serialization import value_from_json_encodable

logger = logging.getLogger(__name__)


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


def get_artifact(artifact_id: str) -> Artifact:
    """
    Get an artifact from the database.

    Parameters
    ----------
    artifact_id : str
        ID of artifact to retrieve.

    Returns
    -------
    Artifact
        Fetched artifact
    """
    with db().get_session() as session:
        return session.query(Artifact).filter(Artifact.id == artifact_id).one()


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


def get_run_status_details(
    run_ids: List[str],
) -> Dict[str, Tuple[FutureState, List[ExternalJob]]]:
    """
    Get information about runs' statuses from the DB.

    This is an optimization to enable getting only status-related information
    about the runs, and should only be preferred to get_run when the query
    happens often and only involves statuses.

    Parameters
    ----------
    run_ids :
        ID of runs whose status should be retrieved

    Returns
    -------
    A dict whose keys are run ids. The values are tuples where the first element
    is the future state for the run and the second element is a list of external
    jobs for the run (if any exist)
    """
    with db().get_session() as session:
        query_results = (
            session.query(Run.id, Run.future_state, Run.external_jobs_json)
            .filter(Run.id.in_(run_ids))
            .all()
        )
        result_dict = {}
        for run_id, state_string, jobs_encodable in query_results:
            if jobs_encodable is None:
                jobs = []
            else:
                jobs = [
                    value_from_json_encodable(job, ExternalJob)
                    for job in jobs_encodable
                ]
            result_dict[run_id] = (FutureState[state_string], jobs)
    return result_dict


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
    _assert_external_jobs_not_removed([run])
    with db().get_session() as session:
        session.add(run)
        session.commit()
        session.refresh(run)

    return run


def get_resolution(resolution_id: str) -> Resolution:
    """Get a resolution from the database.

    Parameters
    ----------
    resolution_id:
        ID of resoution to retrieve.

    Returns
    -------
    Fetched resolution
    """
    with db().get_session() as session:
        return (
            session.query(Resolution).filter(Resolution.root_id == resolution_id).one()
        )


def save_resolution(resolution: Resolution) -> Resolution:
    """Save resolution to the database.

    Parameters
    ----------
    resolution:
        Resolution to save

    Returns
    -------
    saved resolution
    """
    with db().get_session() as session:
        session.merge(resolution)
        session.commit()

    return resolution


def save_graph(runs: List[Run], artifacts: List[Artifact], edges: List[Edge]):
    """
    Update a graph
    """
    _assert_external_jobs_not_removed(runs)
    with db().get_session() as session:
        for run in runs:
            session.merge(run)

        for artifact in artifacts:
            session.merge(artifact)

        for edge in edges:
            session.merge(edge)

        session.commit()


def _assert_external_jobs_not_removed(runs):
    run_ids = [run.id for run in runs]
    runs_by_id = {run.id: run for run in runs}
    with db().get_session() as session:
        existing_run_jobs_all_runs = (
            session.query(Run.id, Run.external_jobs_json)
            .filter(Run.id.in_(run_ids))
            .all()
        )

        # it's ok if there isn't an existing run for one of the passed-in runs.
        # the passed-in runs may be new.
        for existing_run_id, existing_run_jobs_json in existing_run_jobs_all_runs:
            if existing_run_jobs_json is None:
                existing_run_jobs = []
            else:
                existing_run_jobs = [
                    value_from_json_encodable(job, ExternalJob)
                    for job in existing_run_jobs_json
                ]
            run = runs_by_id[existing_run_id]
            if len(run.external_jobs) < len(existing_run_jobs):
                raise ValueError(
                    f"Cannot remove existing external jobs from {run.id}. "
                    f"Existing run had: {existing_run_jobs}. New "
                    f"run had: {run.external_jobs}"
                )


Graph = Tuple[List[Run], List[Artifact], List[Edge]]


def get_run_graph(run_id: str) -> Graph:
    """
    Get run graph.

    This will return the run's direct graph, meaning
    only edges directly connected to it, and their corresponding artifacts.
    """
    return get_graph(Run.id == run_id)


def get_root_graph(root_id: str) -> Graph:
    """
    Get entire graph for root_id.

    This will return the entire graph for a given root_id.
    """
    return get_graph(Run.root_id == root_id)


def get_graph(
    run_predicate: ColumnElement,
    include_edges: bool = True,
    include_artifacts: bool = True,
) -> Graph:
    """
    Retrieve the graph for a run predicate
    (e.g. Run.root_id == root_id, or Run.id == run_id)
    """
    with db().get_session() as session:
        runs: List[Run] = session.query(Run).filter(run_predicate).all()
        run_ids = [run.id for run in runs]

        edges: List[Edge] = []
        if include_edges:
            edges = (
                session.query(Edge)
                .filter(
                    sqlalchemy.or_(
                        Edge.source_run_id.in_(run_ids),
                        Edge.destination_run_id.in_(run_ids),
                    )
                )
                .all()
            )

        artifacts: List[Artifact] = []
        if include_artifacts:
            artifact_ids = {
                edge.artifact_id for edge in edges if edge.artifact_id is not None
            }
            artifacts = (
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


# DO NOT USE
# This query is more optimal than the one in `get_graph` (single query)
# but has corner cases when some runs have no edges or artifacts
# Use `get_graph` instead
def _get_root_graph(root_run_id: str) -> Tuple[Set[Run], Set[Edge], Set[Artifact]]:
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


def get_user(email: str) -> User:
    """
    Get a user from the DB.
    """
    with db().get_session() as session:
        return session.query(User).filter(User.email == email).one()


def get_user_by_api_key(api_key: str) -> User:
    """
    Get a user by API key
    """
    with db().get_session() as session:
        return session.query(User).filter(User.api_key == api_key).one()


def save_user(user: User) -> User:
    """
    Save a user to the DB
    """
    with db().get_session() as session:
        session.add(user)
        session.commit()
        session.refresh(user)

    return user
