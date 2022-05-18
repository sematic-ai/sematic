"""
Module holding common DB queries.
"""
# Standard library
import datetime
import typing

# Third-party
import sqlalchemy
import sqlalchemy.orm

# Glow
from glow.abstract_future import FutureState
from glow.db.models.artifact import Artifact
from glow.db.models.run import Run
from glow.db.db import db
from glow.db.models.run_artifact import RunArtifact, RunArtifactRelationship


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


def create_run_with_artifacts(run: Run, artifacts: typing.Dict[str, Artifact]) -> Run:
    """
    Create a run and its input artifacts.

    Parameters
    ----------
    run: Run
        Run to create
    artifacts: Dict[str, Artifact]
        Mapping of input argument name to artifact

    Returns
    -------
    Run
        persisted run
    """
    with db().get_session() as session:
        session.add(run)

        for name, artifact in artifacts.items():
            artifacts[name] = _add_unique_artifact(session, artifact)

            run_artifact = RunArtifact(
                run_id=run.id,
                artifact_id=artifact.id,
                name=name,
                relationship=RunArtifactRelationship.INPUT.value,
            )

            session.add(run_artifact)

        session.commit()
        session.refresh(run)

        for artifact in artifacts.values():
            session.refresh(artifact)

    return run


def get_run_output_artifact(run_id: str) -> typing.Optional[Artifact]:
    """Get a run's output artifact."""
    artifacts = get_run_artifacts(run_id, RunArtifactRelationship.OUTPUT)
    if artifacts:
        return artifacts[0]

    return None


def get_run_input_artifacts(run_id: str) -> typing.Dict[typing.Text, Artifact]:
    """Get a mapping of a run's input artifacts."""
    artifacts_by_id = {
        artifact.id: artifact
        for artifact in get_run_artifacts(run_id, RunArtifactRelationship.INPUT)
    }

    with db().get_session() as session:
        run_artifacts: typing.List[RunArtifact] = (
            session.query(RunArtifact)
            .filter(
                sqlalchemy.and_(
                    RunArtifact.run_id == run_id,
                    RunArtifact.relationship == RunArtifactRelationship.INPUT.value,
                )
            )
            .all()
        )

    return {
        run_artifact.name: artifacts_by_id[run_artifact.artifact_id]
        for run_artifact in run_artifacts
    }


def get_run_artifacts(
    run_id: str, relationship: typing.Optional[RunArtifactRelationship] = None
) -> typing.Tuple[Artifact, ...]:
    """Get artifacts associated with a run."""
    run_artifact_filter = [RunArtifact.run_id == run_id]
    if relationship:
        run_artifact_filter.append(RunArtifact.relationship == relationship.value)

    with db().get_session() as session:
        artifacts: typing.List[Artifact] = (
            session.query(Artifact)
            .join(RunArtifact)
            .filter(sqlalchemy.and_(*run_artifact_filter))
            .all()
        )

    return tuple(artifacts)


def set_run_output_artifact(run: Run, artifact: Artifact) -> None:
    """
    Sets the output artifact and updates the run state in the same
    transaction
    """
    run.future_state = FutureState.RESOLVED.value
    run.resolved_at = datetime.datetime.utcnow()

    if run.ended_at is None:
        run.ended_at = run.resolved_at

    run_artifact = RunArtifact(
        run_id=run.id,
        artifact_id=artifact.id,
        relationship=RunArtifactRelationship.OUTPUT.value,
    )

    with db().get_session() as session:
        artifact = _add_unique_artifact(session, artifact)
        session.add(artifact)
        session.flush()
        session.add(run)
        session.add(run_artifact)
        session.commit()
        session.refresh(run)
        session.refresh(artifact)


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
