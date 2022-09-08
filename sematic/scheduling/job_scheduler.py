# Standard Library
from typing import List, Optional, Tuple

# Sematic
from sematic.abstract_future import FutureState
from sematic.db.models.resolution import Resolution, ResolutionStatus
from sematic.db.models.run import Run
from sematic.scheduling import kubernetes as k8s
from sematic.scheduling.external_job import KUBERNETES_JOB_KIND, ExternalJob


class RunStateNotSchedulable(Exception):
    """The run is not in a state that would allow it to be scheduled."""

    pass


def schedule_run(run: Run, resolution: Resolution) -> Run:
    """Start a job for the run on external compute.

    Parameters
    ----------
    run:
        The run to schedule
    resolution:
        The resolution associated with the run
    """
    run.external_jobs = _refresh_external_jobs(run.external_jobs)
    _validate_scheduleable(run, resolution)
    run.external_jobs.append(_schedule_job(run, resolution))
    return run


def update_run_status(
    future_state: FutureState, external_jobs: List[ExternalJob]
) -> Tuple[FutureState, Optional[str]]:
    """Determine whether a new run state should be used based ONLY external job statuses

    The external jobs themselves will have their state information refreshed before
    determining whether the run needs its status changed.

    Parameters
    ----------
    future_state:
        The current state of the run
    external_jobs:
        The external jobs associated with the run.
    """
    if future_state.is_terminal():
        return future_state, None
    if future_state.value == FutureState.RAN.value:
        return future_state, None
    if future_state.value == FutureState.CREATED.value:
        if len(external_jobs) == 0:
            return future_state, None
        else:
            raise ValueError(
                "Run is in an invalid state: it is marked as CREATED but it has "
                "external jobs. Runs with external jobs should be SCHEDULED."
            )
    external_jobs = _refresh_external_jobs(external_jobs)
    if future_state.value == FutureState.SCHEDULED.value:
        if not any(job.is_active() for job in external_jobs):
            return (
                FutureState.FAILED,
                "The kubernetes job(s) experienced an unknown failure",
            )
    raise ValueError(
        f"Future is in a state not covered by update logic: {future_state}"
    )


def _validate_scheduleable(run: Run, resolution: Resolution):
    if run.future_state != FutureState.CREATED.value:
        raise RunStateNotSchedulable(
            f"The run {run.id} was in the state {run.future_state}, and could "
            f"not be scheduled. Runs can only be scheduled if they are in the "
            f"{FutureState.CREATED} state."
        )
    for job in run.external_jobs:
        if job.is_active():
            raise RunStateNotSchedulable(
                f"The run {run.id} already had an active external job "
                f"{job.external_job_id} and thus could not be scheduled."
            )
    if resolution.status != ResolutionStatus.RUNNING.value:
        raise RunStateNotSchedulable(
            f"The run {run.id} was not schedulable because there "
            f"is no active resolution for it."
        )
    if resolution.docker_image_uri is None:
        raise RunStateNotSchedulable(
            f"The resolution {resolution.root_id} had no docker image URI"
        )
    # TODO(#98): assert run has resource requirements that are specified


def _refresh_external_jobs(jobs: Optional[List[ExternalJob]]):
    jobs = jobs if jobs is not None else []
    refreshed = []
    for job in jobs:
        if not job.is_active():
            refreshed.append(job)
            continue
        job = _refresh_external_job(job)
        refreshed.append(job)
    return refreshed


def _refresh_external_job(job: ExternalJob) -> ExternalJob:
    if job.kind != KUBERNETES_JOB_KIND:
        raise RuntimeError("Can only support Kubernetes jobs to fulfill runs.")
    if not job.is_active():
        return job
    return k8s.refresh_job(job)


def _schedule_job(run: Run, resolution: Resolution) -> ExternalJob:
    # k8s is the only thing we can submit jobs to at the moment.

    # should be impossible to fail this assert, but it makes mypy happy
    assert resolution.docker_image_uri is not None
    return k8s.schedule_run_job(
        run_id=run.id,
        image=resolution.docker_image_uri,
        user_settings=resolution.settings_env_vars,
        resource_requirements=None,
        try_number=len(run.external_jobs),
    )
