# Standard Library
import logging
from enum import Enum, unique
from typing import Iterable, List, Optional, Sequence, Tuple

# Sematic
from sematic.abstract_future import FutureState
from sematic.db.models.job import Job
from sematic.db.models.resolution import Resolution, ResolutionStatus
from sematic.db.models.run import Run
from sematic.db.queries import save_job
from sematic.scheduling import kubernetes as k8s
from sematic.scheduling.job_details import KubernetesJobState
from sematic.versions import MIN_CLIENT_SERVER_SUPPORTS, string_version_to_tuple

logger = logging.getLogger(__name__)


class StateNotSchedulable(Exception):
    """The run or resolution is not in a state that would allow it to be scheduled."""

    pass


def schedule_run(
    run: Run, resolution: Resolution, existing_jobs: Sequence[Job]
) -> Tuple[Run, List[Job]]:
    """Start a job for the run on external compute.

    A new `Job` object will be appended to the end of the jobs for the
    run describing the new job details.

    Parameters
    ----------
    run:
        The run to schedule.
    resolution:
        The resolution associated with the run.
    existing_jobs:
        Any existent jobs associated with the run.

    Returns
    -------
    A tuple where the first element is the run with its status updated and
    the second element is the new list of jobs associated with the run.
    """
    # before scheduling a new run, update the information about previous runs
    existing_jobs = _refresh_jobs(existing_jobs)
    _assert_is_scheduleable(run, resolution, existing_jobs)
    jobs = list(existing_jobs) + [_schedule_job(run, resolution, existing_jobs)]
    run.future_state = FutureState.SCHEDULED
    logger.info("After schedule, jobs: %s", jobs)  # TODO: remove
    return (run, jobs)


def schedule_resolution(
    resolution: Resolution,
    max_parallelism: Optional[int] = None,
    rerun_from: Optional[str] = None,
) -> Tuple[Resolution, Job]:
    """Start a resolution for the run on external compute.

    Parameters
    ----------
    resolution: Resolution
        The resolution associated with the run.
    max_parallelism:
        The maximum number of non-inlined runs that the resolver will allow to be in the
        SCHEDULED state at any one time.
    rerun_from: Optional[str]
        Start resolution from a particular point.

    Returns
    -------
    A tuple where the first element is the resolution with its status updated and
    the second is the job associated with the resolution.
    """
    _assert_resolution_is_scheduleable(resolution)
    job = _schedule_resolution_job(
        resolution=resolution,
        max_parallelism=max_parallelism,
        rerun_from=rerun_from,
    )

    resolution.status = ResolutionStatus.SCHEDULED
    return (resolution, job)


def update_run_status(
    future_state: FutureState,
    jobs: Sequence[Job],
) -> Tuple[FutureState, Sequence[Job]]:
    """Determine whether a new run state should be used based ONLY on job statuses.

    The jobs themselves will have their state information refreshed before
    determining whether the run needs its status changed.

    Parameters
    ----------
    future_state:
        The current state of the run.
    jobs:
        The jobs associated with the run.

    Returns
    -------
    A tuple with 2 elements. The first is the new future state (same state if unchanged).
    The second is the updated jobs tuple.
    """
    active_jobs_remain = any(job.latest_status.is_active() for job in jobs)
    if future_state.is_terminal():
        if active_jobs_remain:
            logger.warning(
                "There are still active jobs for run in "
                "state %s (will refresh jobs): %s",
                future_state,
                jobs,
            )
            refreshed_jobs = _refresh_jobs(jobs)
            logger.warning(
                "After refresh, jobs are: " "%s",
                refreshed_jobs,
            )
            return future_state, refreshed_jobs
        else:
            return future_state, jobs

    if future_state.value == FutureState.RAN.value:
        # If the job already RAN, the only reason it's not
        # terminal is because child runs have to complete.
        # There should be no more jobs for this run.
        return future_state, jobs

    if future_state.value == FutureState.CREATED.value:
        if len(jobs) == 0:
            return future_state, jobs
        else:
            raise ValueError(
                "Run is in an invalid state: it is marked as CREATED but it has "
                "jobs. Runs with jobs should be SCHEDULED."
            )
    if len(jobs) < 1:
        raise ValueError("No jobs for run")

    jobs = _refresh_jobs(jobs)

    if future_state.value == FutureState.SCHEDULED.value:
        if jobs[-1].latest_status.is_active():
            return FutureState.SCHEDULED, jobs

        job_summary_str = "\n ".join([repr(job) for job in jobs])
        exception_metadata = jobs[-1].details.get_exception_metadata()
        logger.warning(
            "Job failed due to K8s job failure:\n%s\nJob states:\n%s",
            exception_metadata.repr if exception_metadata is not None else None,
            job_summary_str,
        )

        return FutureState.FAILED, jobs

    raise ValueError(
        f"Future is in a state not covered by update logic: {future_state}"
    )


def _assert_resolution_is_scheduleable(resolution: Resolution):
    """raise StateNotSchedulable if the state is not such that it can be scheduled"""
    if resolution.status != ResolutionStatus.CREATED.value:
        raise StateNotSchedulable(
            f"The resolution {resolution.root_id} was in the state {resolution.status}, "
            f"and could not be scheduled. Resolution can only be scheduled if they "
            f"are in the {ResolutionStatus.CREATED} state."
        )
    if resolution.container_image_uri is None:
        raise StateNotSchedulable(
            f"The resolution {resolution.root_id} had no docker image URI"
        )

    valid_client_version = (
        resolution.client_version is not None
        and string_version_to_tuple(resolution.client_version)
        < MIN_CLIENT_SERVER_SUPPORTS
    )
    if valid_client_version:
        # You may wonder how we can get here given that clients check for server
        # compatibility. This can still happen if somebody tries to rerun an old
        # resolution (ex: from the UI).
        raise StateNotSchedulable(
            f"The resolution {resolution.root_id} uses Sematic version "
            f"{resolution.client_version}, but the server requires at least "
            f"version {MIN_CLIENT_SERVER_SUPPORTS}"
        )


def _assert_is_scheduleable(
    run: Run, resolution: Resolution, existing_jobs: Sequence[Job]
):
    """raise RunStateNotSchedulable if the state is not such that it can be scheduled"""
    if run.future_state not in {FutureState.CREATED.value, FutureState.RETRYING.value}:
        raise StateNotSchedulable(
            f"The run {run.id} was in the state {run.future_state}, and could "
            f"not be scheduled. Runs can only be scheduled if they are in the "
            f"{FutureState.CREATED} state."
        )

    for job in existing_jobs:
        if (
            job.latest_status.is_active()
            and run.future_state != FutureState.RETRYING.value
        ):
            raise StateNotSchedulable(
                f"The run {run.id} already had an active job "
                f"{job.namespace}/{job.name} and thus could not be scheduled."
            )
    if resolution.status != ResolutionStatus.RUNNING.value:
        raise StateNotSchedulable(
            f"The run {run.id} was not schedulable because there "
            f"is no active resolution for it."
        )
    if run.container_image_uri is None:
        raise StateNotSchedulable(f"Run {run.id} has no container image URI")


def _refresh_jobs(jobs: Iterable[Job]) -> Sequence[Job]:
    """For any jobs that are still active, refresh them from external compute"""
    refreshed = []
    for job in jobs:
        if not job.latest_status.is_active():
            refreshed.append(job)
            continue
        job = _refresh_job(job)
        refreshed.append(job)
    return refreshed


def _refresh_job(job: Job) -> Job:
    """Reach out to external compute to update the state of the job."""
    # modify a new copy, not existing one
    job = Job.from_json_encodable(job.to_json_encodable(redact=False))

    if not job.latest_status.is_active():
        return job
    return k8s.refresh_job(job)


def _schedule_job(
    run: Run, resolution: Resolution, existing_jobs: Sequence[Job]
) -> Job:
    """Reach out to external compute to start the execution of the run"""
    # k8s is the only thing we can submit jobs to at the moment.

    # should be impossible to fail this assert, but it makes mypy happy
    if run.container_image_uri is None:
        raise ValueError(f"Run {run.id} is missing a container image")

    return k8s.schedule_run_job(
        run_id=run.id,
        image=run.container_image_uri,
        user_settings=resolution.settings_env_vars,
        resource_requirements=run.resource_requirements,
        try_number=len(existing_jobs),
    )


def _schedule_resolution_job(
    resolution: Resolution,
    max_parallelism: Optional[int] = None,
    rerun_from: Optional[str] = None,
) -> Job:
    """Reach out to external compute to start the execution of the resolution"""
    # should be impossible to fail this assert, but it makes mypy happy
    assert resolution.container_image_uri is not None
    return k8s.schedule_resolution_job(
        resolution_id=resolution.root_id,
        image=resolution.container_image_uri,
        user_settings=resolution.settings_env_vars,
        max_parallelism=max_parallelism,
        rerun_from=rerun_from,
    )


@unique
class JobCleaningStateChange(Enum):
    DELETED = "DELETED"
    UNMODIFIED = "UNMODIFIED"
    DELETION_ERROR = "DELETION_ERROR"
    FORCE_DELETED = "FORCE_DELETED"


def clean_jobs(jobs: List[Job], force: bool) -> List[JobCleaningStateChange]:
    changes = []
    for job in jobs:
        if job.state in KubernetesJobState.terminal_states():
            changes.append(JobCleaningStateChange.UNMODIFIED)
            logger.info("Leaving job %s unmodified", job.identifier())
            continue
        try:
            logger.info("Cleaning job %s", job.identifier())
            canceled_job = k8s.cancel_job(job)
            save_job(canceled_job)
            changes.append(JobCleaningStateChange.DELETED)
        except Exception:
            logger.exception("Error cleaning job %s", job.identifier())
            if force:
                try:
                    logger.info("Force cleaning job %s", job.identifier())
                    details = job.details
                    details = details.force_clean()
                    job.details = details
                    save_job(job)
                    changes.append(JobCleaningStateChange.FORCE_DELETED)
                except Exception:
                    logger.exception("Could not force-delete job %s", job.identifier())
                    changes.append(JobCleaningStateChange.DELETION_ERROR)
            else:
                changes.append(JobCleaningStateChange.DELETION_ERROR)

    return changes
