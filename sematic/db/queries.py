"""
Module holding common DB queries.
"""
# Standard library
from typing import List, Optional, Dict, Set, Tuple

# Third-party
import sqlalchemy
import sqlalchemy.orm

# Sematic
from sematic.db.models.artifact import Artifact
from sematic.db.models.edge import Edge
from sematic.db.models.run import Run
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


def create_run_with_artifacts(run: Run, artifacts: Dict[str, Artifact]) -> Run:
    edges = [
        Edge(destination_run_id=run.id, destination_name=name, artifact_id=artifact.id)
        for name, artifact in artifacts.items()
    ]
    save_graph([run], list(artifacts.values()), edges)
    return run


def set_run_output_artifact(run, artifact):
    edge = Edge(source_run_id=run.id, artifact_id=artifact.id)
    save_graph([run], [artifact], [edge])


def save_graph(runs: List[Run], artifacts: List[Artifact], edges: List[Edge]):
    unique_artifacts = []
    with db().get_session() as session:
        session.add_all(runs)
        unique_artifacts = [
            _add_unique_artifact(session, artifact) for artifact in artifacts
        ]

        # session.flush()
        session.add_all(edges)
        session.commit()

        for run in runs:
            session.refresh(run)

        for artifact in unique_artifacts:
            session.refresh(artifact)

        for edge in edges:
            session.refresh(edge)


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


def get_run_output_artifact(run_id: str) -> Optional[Artifact]:
    """Get a run's output artifact."""
    with db().get_session() as session:
        return (
            session.query(Artifact)
            .join(Edge, Edge.artifact_id == Artifact.id)
            .filter(Edge.source_run_id == run_id)
            .first()
        )


def get_run_input_artifacts(run_id: str) -> Dict[str, Artifact]:
    """Get a mapping of a run's input artifacts."""
    with db().get_session() as session:
        edges = set(
            session.query(Edge)
            .with_entities(Edge.artifact_id, Edge.destination_name)
            .filter(Edge.destination_run_id == run_id)
            .all()
        )
        artifact_ids = set(edge.artifact_id for edge in edges)
        artifacts = session.query(Artifact).filter(Artifact.id.in_(artifact_ids)).all()
        artifacts_by_id = {artifact.id: artifact for artifact in artifacts}

        return {
            edge.destination_name: artifacts_by_id[edge.artifact_id] for edge in edges
        }


def get_root_graph(root_run_id: str) -> Tuple[Set[Run], Set[Edge], Set[Artifact]]:
    import logging

    logging.basicConfig()
    logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
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


def _add_unique_artifact(
    session: sqlalchemy.orm.Session, artifact: Artifact
) -> Artifact:
    existing_artifact = (
        session.query(Artifact).filter(Artifact.id == artifact.id).first()
    )

    if existing_artifact is None:
        session.add(artifact)
    else:
        artifact = existing_artifact

    return artifact
