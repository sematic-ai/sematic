# Standard Library
import logging
from dataclasses import replace
from typing import Iterable, List, Optional, Tuple, Union

# Sematic
from sematic.abstract_future import FutureState
from sematic.db.models.resolution import Resolution, ResolutionStatus
from sematic.db.models.run import Run
from sematic.scheduling import kubernetes as k8s
from sematic.scheduling.external_job import KUBERNETES_JOB_KIND, ExternalJob

logger = logging.getLogger(__name__)


class StateNotSchedulable(Exception):
    """The run or resolution is not in a state that would allow it to be scheduled."""

    pass


def schedule_run(run: Run, resolution: Resolution) -> Run:
    """Start a job for the run on external compute.

    A new `ExternalJob` object will be appended to the end of the run's `external_jobs`
    field describing the new job details.

    Parameters
    ----------
    run:
        The run to schedule
    resolution:
        The resolution associated with the run
    """
    # before scheduling a new run, update the information about previous runs
    run.external_jobs = _refresh_external_jobs(run.external_jobs)
    _assert_is_scheduleable(run, resolution)
    external_jobs_list = list(run.external_jobs) + [_schedule_job(run, resolution)]
    run.external_jobs = tuple(external_jobs_list)
    run.future_state = FutureState.SCHEDULED
    return run


def schedule_resolution(
    resolution: Resolution,
    max_parallelism: Optional[int] = None,
    rerun_from: Optional[str] = None,
) -> Resolution:
    """Start a resolution for the run on external compute.

    Parameters
    ----------
    resolution: Resolution
        The resolution associated with the run
    max_parallelism:
        The maximum number of non-inlined runs that the resolver will allow to be in the
        SCHEDULED state at any one time.
    rerun_from: Optional[str]
        Start resolution from a particular point
    """
    resolution.external_jobs = _refresh_external_jobs(resolution.external_jobs)
    _assert_resolution_is_scheduleable(resolution)
    external_jobs_list = list(resolution.external_jobs) + [
        _schedule_resolution_job(
            resolution=resolution,
            max_parallelism=max_parallelism,
            rerun_from=rerun_from,
        )
    ]
    resolution.external_jobs = tuple(external_jobs_list)
    resolution.status = ResolutionStatus.SCHEDULED
    return resolution


def update_run_status(
    future_state: FutureState,
    external_jobs: Union[List[ExternalJob], Tuple[ExternalJob, ...]],
) -> Tuple[FutureState, Tuple[ExternalJob, ...]]:
    """Determine whether a new run state should be used based ONLY on external job
    statuses.

    The external jobs themselves will have their state information refreshed before
    determining whether the run needs its status changed.

    Parameters
    ----------
    future_state:
        The current state of the run.
    external_jobs:
        The external jobs associated with the run.

    Returns
    -------
    A tuple with 2 elements. The first is the new future state (same state if unchanged).
    The second is the updated external jobs tuple.
    """
    external_jobs = tuple(external_jobs)
    if future_state.is_terminal():
        return future_state, external_jobs

    if future_state.value == FutureState.RAN.value:
        # If the job already RAN, the only reason it's not
        # terminal is because child runs have to complete.
        # There should be no more external jobs for this run.
        return future_state, external_jobs

    if future_state.value == FutureState.CREATED.value:
        if len(external_jobs) == 0:
            return future_state, external_jobs
        else:
            raise ValueError(
                "Run is in an invalid state: it is marked as CREATED but it has "
                "external jobs. Runs with external jobs should be SCHEDULED."
            )
    if len(external_jobs) < 1:
        raise ValueError("No external jobs for run")

    external_jobs = _refresh_external_jobs(external_jobs)

    if future_state.value == FutureState.SCHEDULED.value:
        if external_jobs[-1].is_active():
            return FutureState.SCHEDULED, external_jobs

        job_summary_str = "\n ".join([repr(job) for job in external_jobs])
        exception_metadata = external_jobs[-1].get_exception_metadata()
        logger.warning(
            "Job failed due to K8s job failure:\n%s\nJob states:\n%s",
            exception_metadata.repr if exception_metadata is not None else None,
            job_summary_str,
        )

        return FutureState.FAILED, external_jobs

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
    for job in resolution.external_jobs:
        if job.is_active():
            raise StateNotSchedulable(
                f"The resolution {resolution.root_id} already had an active external "
                f"job {job.external_job_id} and thus could not be scheduled."
            )
    if resolution.container_image_uri is None:
        raise StateNotSchedulable(
            f"The resolution {resolution.root_id} had no docker image URI"
        )


def _assert_is_scheduleable(run: Run, resolution: Resolution):
    """raise RunStateNotSchedulable if the state is not such that it can be scheduled"""
    if run.future_state not in {FutureState.CREATED.value, FutureState.RETRYING.value}:
        raise StateNotSchedulable(
            f"The run {run.id} was in the state {run.future_state}, and could "
            f"not be scheduled. Runs can only be scheduled if they are in the "
            f"{FutureState.CREATED} state."
        )

    for job in run.external_jobs:
        if job.is_active() and run.future_state != FutureState.RETRYING.value:
            raise StateNotSchedulable(
                f"The run {run.id} already had an active external job "
                f"{job.external_job_id} and thus could not be scheduled."
            )
    if resolution.status != ResolutionStatus.RUNNING.value:
        raise StateNotSchedulable(
            f"The run {run.id} was not schedulable because there "
            f"is no active resolution for it."
        )
    if run.container_image_uri is None:
        raise StateNotSchedulable(f"Run {run.id} has no container image URI")


def _refresh_external_jobs(jobs: Iterable[ExternalJob]) -> Tuple[ExternalJob, ...]:
    """For any external jobs that are still active, refresh them from external compute"""
    refreshed = []
    for job in jobs:
        if not job.is_active():
            refreshed.append(job)
            continue
        job = _refresh_external_job(job)
        refreshed.append(job)
    return tuple(refreshed)


def _refresh_external_job(job: ExternalJob) -> ExternalJob:
    """Reach out to external compute to update the state of the external job"""
    if job.kind != KUBERNETES_JOB_KIND:
        raise RuntimeError("Can only support Kubernetes jobs to fulfill runs.")
    job = replace(job)  # modify new copy, not existing one
    if not job.is_active():
        return job
    return k8s.refresh_job(job)


def _schedule_job(run: Run, resolution: Resolution) -> ExternalJob:
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
        try_number=len(run.external_jobs),
    )


def _schedule_resolution_job(
    resolution: Resolution,
    max_parallelism: Optional[int] = None,
    rerun_from: Optional[str] = None,
) -> ExternalJob:
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
