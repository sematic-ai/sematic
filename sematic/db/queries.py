"""
Module holding common DB queries.
"""
# Standard Library
import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Set, Tuple

# Third-party
import sqlalchemy
import sqlalchemy.orm
from sqlalchemy.sql.elements import ColumnElement

# Sematic
from sematic.abstract_future import FutureState
from sematic.db.db import db
from sematic.db.models.artifact import Artifact
from sematic.db.models.edge import Edge
from sematic.db.models.external_resource import ExternalResource
from sematic.db.models.job import Job
from sematic.db.models.note import Note
from sematic.db.models.resolution import Resolution, ResolutionStatus
from sematic.db.models.run import Run
from sematic.db.models.runs_external_resource import RunExternalResource
from sematic.db.models.user import User
from sematic.plugins.abstract_external_resource import ManagedBy, ResourceState
from sematic.scheduling.job_details import JobKind, JobKindString, KubernetesJobState
from sematic.utils.exceptions import IllegalStateTransitionError

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


def get_users(user_ids: List[str]) -> List[User]:
    """
    Get users from the database.

    Parameters
    ----------
    user_ids: List[str]
        List of IDs to retrieve.

    Returns
    -------
    List[User]
        List of users
    """
    with db().get_session() as session:
        return session.query(User).filter(User.id.in_(list(set(user_ids)))).all()


def get_user(user_id: str) -> User:
    """
    Get a user from the database.

    Parameters
    ----------
    user_id : str
        ID of user to retrieve.

    Returns
    -------
    User
        Fetched user
    """
    with db().get_session() as session:
        return session.query(User).filter(User.id == user_id).one()


def get_user_by_email(email: str) -> User:
    """
    Get a user from the database by email.

    Parameters
    ----------
    email : str
        email of user to retrieve.

    Returns
    -------
    User
        Fetched user
    """
    with db().get_session() as session:
        return session.query(User).filter(User.email == email).one()


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


def get_existing_run_ids(run_ids: Iterable[str]) -> Set[str]:
    """
    From a list of run IDs, return a set of the ones that exist in the DB.

    Parameters
    ----------
    run_ids: Iterable[str]
        List of run IDs to check for existence.

    Returns
    -------
    Set[str]
        The set of existing run IDs.
    """
    with db().get_session() as session:
        existing_run_ids = session.query(Run.id).filter(Run.id.in_(run_ids)).all()

    return set([row[0] for row in existing_run_ids])


def get_run_status_details(
    run_ids: List[str],
) -> Dict[str, Tuple[FutureState, List[Job]]]:
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
        query_results = list(
            session.query(Run.id, Run.future_state, Job)
            .outerjoin(Job, Job.run_id == Run.id, full=True)
            .filter(Run.id.in_(run_ids))
            # Job kind can be None when there are no jobs for the run yet.
            # We still want to return the future state in that case. No actual
            # row in the Job table will have a null kind/null run id.
            # It appears that way here merely due to the outer join.
            .filter(sqlalchemy.or_(Job.kind == JobKind.run, Job.kind.is_(None)))
            .all()
        )

        run_ids_to_jobs_list = defaultdict(list)
        for run_id, _, job in query_results:
            if job is None:
                continue
            run_ids_to_jobs_list[run_id].append(job)

    future_state_and_jobs_by_run_id: Dict[str, Tuple[FutureState, List[Job]]] = {
        run_id: (FutureState[future_state], run_ids_to_jobs_list[run_id])
        for run_id, future_state, _ in query_results  # type: ignore
    }
    return future_state_and_jobs_by_run_id


def get_calculator_path(run_id: str) -> str:
    with db().get_session() as session:
        row = session.query(Run.calculator_path).filter(Run.id == run_id).one()

    return row[0]


@dataclass
class BasicPipelineMetrics:
    count_by_state: Dict[str, int]
    avg_runtime_children: Dict[str, float]
    total_count: int


def get_basic_pipeline_metrics(calculator_path: str):
    with db().get_session() as session:
        count_by_state = list(
            session.query(Run.future_state, sqlalchemy.func.count())
            .filter(Run.calculator_path == calculator_path)
            .group_by(Run.future_state)
        )

        RootRun = sqlalchemy.orm.aliased(Run)
        avg_runtime_children = list(
            session.query(
                Run.calculator_path,
                sqlalchemy.func.avg(
                    sqlalchemy.func.extract("epoch", Run.resolved_at)
                    - sqlalchemy.func.extract("epoch", Run.started_at)
                ),
            )
            .join(RootRun, Run.root_id == RootRun.id)
            .filter(
                RootRun.calculator_path == calculator_path, Run.resolved_at is not None
            )
            .group_by(Run.calculator_path)
        )

    total_count = sum([count for _, count in count_by_state])

    return BasicPipelineMetrics(
        total_count=total_count,
        count_by_state={state: count for state, count in count_by_state},
        avg_runtime_children={path: runtime for path, runtime in avg_runtime_children},
    )


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
        existing_run_future_state = (
            session.query(Run.future_state).filter(Run.id == run.id).one_or_none()
        )
        existing_run_future_state = (
            existing_run_future_state[0]
            if existing_run_future_state is not None
            else None
        )
        new_state = run.future_state
        if isinstance(new_state, FutureState):
            # despite run.future_state being typed as FutureState, it
            # is sometimes a string.
            new_state = new_state.name  # type: ignore

        if (
            existing_run_future_state != new_state
            and not FutureState.is_allowed_transition(
                existing_run_future_state, run.future_state
            )
        ):
            raise IllegalStateTransitionError(
                f"Cannot transition run from '{existing_run_future_state}' to "
                f"'{run.future_state}'"
            )
        session.add(run)
        session.commit()
        session.refresh(run)

    return run


def get_job(job_name: str, job_namespace: str) -> Optional[Job]:
    """Get a job by name and namespace (or None if it doesn't exist)."""
    with db().get_session() as session:
        return (
            session.query(Job)
            .filter(Job.name == job_name)
            .filter(Job.namespace == job_namespace)
            .one_or_none()
        )


def save_job(job: Job) -> Job:
    """Save a job to the db, updating an existing one if present."""
    with db().get_session() as session:
        # do this instead of get_job so we can keep it in one
        # session to avoid race conditions.
        existing_job = (
            session.query(Job)
            .filter(Job.name == job.name)
            .filter(Job.namespace == job.namespace)
            .one_or_none()
        )

        if existing_job is not None:
            # do this to ensure that we are updating the history based on what's
            # actually already in the DB.
            existing_job.details = job.details
            existing_job.update_status(job.latest_status)
            job = existing_job

        session.merge(job)
        session.commit()

        return job


def get_run_ids_with_orphaned_jobs() -> List[str]:
    with db().get_session() as session:
        query_results = list(
            session.query(
                Job.run_id,
                sqlalchemy.func.max(Job.kind),
                sqlalchemy.func.max(Job.state),
                sqlalchemy.func.max(Run.id),
                sqlalchemy.func.max(Run.future_state),
            )
            .filter(Job.run_id == Run.id)
            .filter(Job.kind == JobKind.run)
            .filter(
                Run.future_state.in_(
                    [state.value for state in FutureState.terminal_states()]
                )
            )
            .filter(Job.state.not_in(KubernetesJobState.terminal_states()))
            .group_by(Job.run_id)
            .all()
        )
        run_ids = []
        for _, __, job_state, run_id, future_state in query_results:
            logger.info(
                "Run %s in state %s has orphaned job in state %s",
                run_id,
                future_state,
                job_state,
            )
            run_ids.append(run_id)
    return list(run_ids)


def get_resolution_ids_with_orphaned_jobs() -> List[str]:
    with db().get_session() as session:
        query_results = list(
            session.query(
                Job.run_id, Job.kind, Job.state, Resolution.root_id, Resolution.status
            )
            .filter(Job.run_id == Resolution.root_id)
            .filter(Job.kind == JobKind.resolver)
            .filter(
                Resolution.status.in_(
                    [status.value for status in ResolutionStatus.terminal_states()]
                )
            )
            .filter(Job.state.not_in(KubernetesJobState.terminal_states()))
            .all()
        )
        resolution_ids = []
        for _, __, job_state, root_id, status in query_results:
            logger.info(
                "Resolution %s in state %s has orphaned job in state %s",
                root_id,
                status,
                job_state,
            )
            resolution_ids.append(root_id)
    return resolution_ids


def get_orphaned_run_ids() -> List[str]:
    """Get runs whose status is non-terminal, but whose resolutions are terminated.

    Returns
    -------
    A list of ids.
    """
    with db().get_session() as session:
        query_results = list(
            session.query(
                Run.id,
                Run.root_id,
                Run.future_state,
                Resolution.status,
                Resolution.root_id,
            )
            .filter(Run.root_id == Resolution.root_id)
            .filter(
                Resolution.status.in_(
                    [status.value for status in ResolutionStatus.terminal_states()]
                )
            )
            .filter(Run.future_state.not_in(FutureState.terminal_state_strings()))
            .all()
        )
        run_ids = []
        for run_id, root_id, run_state, resolution_status, _ in query_results:
            logger.info(
                "Resolution %s in state %s has orphaned run %s in state %s",
                root_id,
                resolution_status,
                run_id,
                run_state,
            )
            run_ids.append(run_id)
    return run_ids


def get_stale_resolution_ids() -> List[str]:
    """Get ids of resolutions that is non-terminal, but whose root runs are.

    Returns
    -------
    A list of ids.
    """
    with db().get_session() as session:
        query_results = list(
            session.query(
                Run.id,
                Run.root_id,
                Run.future_state,
                Resolution.status,
                Resolution.root_id,
            )
            .filter(Run.id == Resolution.root_id)
            .filter(
                Resolution.status.not_in(
                    [status.value for status in ResolutionStatus.terminal_states()]
                )
            )
            .filter(Run.future_state.in_(FutureState.terminal_state_strings()))
            .all()
        )
        resolution_ids = []
        for run_id, root_id, run_state, resolution_status, _ in query_results:
            logger.info(
                "Resolution %s in state %s has root run %s in state %s",
                root_id,
                resolution_status,
                run_id,
                run_state,
            )
            resolution_ids.append(root_id)
    return resolution_ids


def get_jobs_by_run_id(run_id: str, kind: JobKindString = JobKind.run) -> List[Job]:
    """Get jobs from the DB by source run id.

    Parameters
    ----------
    run_id:
        The id of the run to get jobs for
    kind:
        The kind of jobs to get. Can be either "run" to get
        jobs for the run itself, or "resolution" to get jobs
        for the resolution associated with the run.

    Returns
    -------
    The job(s) associated with the run.
    """
    with db().get_session() as session:
        return list(
            session.query(Job)
            .filter(Job.run_id == run_id)
            .filter(Job.kind == kind)
            .all()
        )


def count_jobs_by_run_id(run_id: str, kind: JobKindString = JobKind.run) -> int:
    """Count jobs from the DB by source run id.

    Parameters
    ----------
    run_id:
        The id of the run to get jobs for
    kind:
        The kind of jobs to get. Can be either "run" to get
        jobs for the run itself, or "resolution" to get jobs
        for the resolution associated with the run.

    Returns
    -------
    The number of jobs associated with the run.
    """
    with db().get_session() as session:
        return (
            session.query(Job)
            .filter(Job.run_id == run_id)
            .filter(Job.kind == kind)
            .count()
        )


# TODO: Remove this function
# https://github.com/sematic-ai/sematic/issues/710
# Will also need to be removed if this issue is fixed:
# https://github.com/sematic-ai/sematic/issues/302
def run_has_legacy_jobs(run_id: str) -> bool:
    with db().get_session() as session:
        statement = sqlalchemy.text(
            "SELECT external_jobs_json FROM runs WHERE id=:run_id"
        ).bindparams(run_id=run_id)
        jobs = list(session.execute(statement))[0]["external_jobs_json"]
        return jobs is not None and len(jobs) > 0


def save_external_resource_record(record: ExternalResource):
    """Save an ExternalResource to the DB"""
    if record.resource_state == ResourceState.FORCE_KILLED:
        # There may be problems deserializing the resource.
        # Just save without attempting any complex modifications.
        with db().get_session() as session:
            session.merge(record)
            session.commit()

        return record

    existing_record = get_external_resource_record(record.id)

    if existing_record is None:
        if record.resource_state != ResourceState.CREATED:
            raise ValueError(
                f"Cannot create an external resource in a state other than 'CREATED'. "
                f"{record.id} was in state '{record.resource_state}'."
            )

        # this ensures that all the fields are consistent
        record = ExternalResource.from_resource(record.resource)
    else:
        # this ensures that the update properly updates history
        # and keeps data consistent
        existing_record.resource = record.resource
        record = existing_record

    with db().get_session() as session:
        session.merge(record)
        session.commit()

        return record


def get_external_resource_record(resource_id: str) -> Optional[ExternalResource]:
    """Get an ExternalResource from the DB"""
    with db().get_session() as session:
        return (
            session.query(ExternalResource)
            .filter(ExternalResource.id == resource_id)
            .one_or_none()
        )


def get_orphaned_resource_records() -> List[ExternalResource]:
    """Get ExternalResources orphaned resources from the db.

    Orphaned resources are ones that are not in a terminal state, but
    whose resolutions ARE in a terminal state. This query will only return
    results where the resource is managed by the server or "unknown".
    """
    with db().get_session() as session:
        results = (
            session.query(
                ExternalResource,
                Resolution.root_id,
                RunExternalResource,
                Run.id,
                Run.root_id,
            )
            .filter(ExternalResource.id == RunExternalResource.resource_id)
            .filter(Run.id == RunExternalResource.run_id)
            .filter(Run.root_id == Resolution.root_id)
            .filter(
                ExternalResource.managed_by.in_([ManagedBy.SERVER, ManagedBy.UNKNOWN])
            )
            .filter(
                Resolution.status.in_(
                    [status.value for status in ResolutionStatus.terminal_states()]
                )
            )
            .filter(
                ExternalResource.resource_state.in_(
                    [state for state in ResourceState.non_terminal_states()]
                )
            )
            .all()
        )

        # use a dict based on id: a resource might show up twice if it is used
        # in more than one run.
        resources: Dict[str, ExternalResource] = {}
        for resource, resolution_id, _, run_id, __ in results:
            logger.info(
                "Found orphaned resource '%s' from resolution '%s' and run '%s'",
                resource,
                resolution_id,
                run_id,
            )
            resources[resource.id] = resource
    return list(resources.values())


def save_run_external_resource_links(resource_ids: List[str], run_id: str):
    """Save the relationship between external resources and a run to the DB."""
    with db().get_session() as session:
        for resource_id in resource_ids:
            session.merge(RunExternalResource(resource_id=resource_id, run_id=run_id))
        session.commit()


def get_resources_by_root_id(root_run_id: str) -> List[ExternalResource]:
    """Get a list of external resources associated with a particular root run."""
    with db().get_session() as session:
        results = (
            session.query(ExternalResource, ExternalResource.id)
            .filter(ExternalResource.id == RunExternalResource.resource_id)
            .filter(Run.id == RunExternalResource.run_id)
            .filter(Run.root_id == root_run_id)
            .distinct()
            .all()
        )
        return list(set(r[0] for r in results))


def get_run_ids_for_resource(external_resource_id: str) -> List[str]:
    with db().get_session() as session:
        results = (
            session.query(RunExternalResource.run_id)
            .filter(external_resource_id == RunExternalResource.resource_id)
            .distinct()
            .all()
        )
        return list(r[0] for r in results)


def get_external_resources_by_run_id(run_id: str) -> List[ExternalResource]:
    """
    Get the external resources used by a run.
    """
    with db().get_session() as session:
        external_resources = (
            session.query(ExternalResource)
            .join(
                RunExternalResource,
                sqlalchemy.and_(
                    run_id == RunExternalResource.run_id,
                    ExternalResource.id == RunExternalResource.resource_id,
                ),
            )
            .all()
        )
    return external_resources


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
    Update a graph.
    """
    with db().get_session() as session:
        for run in runs:
            session.merge(run)

        for artifact in artifacts:
            _save_artifact(artifact=artifact, session=session)

        for edge in edges:
            session.merge(edge)

        session.commit()


def _save_artifact(artifact: Artifact, session: sqlalchemy.orm.Session) -> Artifact:
    """
    Saves or updates an Artifact, returning the actual persisted Artifact element.
    """
    previous_artifact = session.get(entity=Artifact, ident=artifact.id)

    if previous_artifact is not None:
        # we use content-addressed values for artifacts, with the id being
        # generated from the type and value themselves
        # there are currently no other fields that can be updated
        logger.debug("Updating existing artifact %s", artifact.id)
        previous_artifact.assert_matches(artifact)
        return previous_artifact

    return session.merge(artifact)


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
