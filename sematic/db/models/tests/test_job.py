# Standard Library
import time
from dataclasses import replace

# Third-party
import pytest

# Sematic
from sematic.db.models.factories import make_job
from sematic.scheduling.job_details import (
    JobDetails,
    JobKind,
    JobStatus,
    KubernetesJobState,
)
from sematic.utils.exceptions import IllegalStateTransitionError


def test_update_status():
    status = JobStatus(
        state=KubernetesJobState.Requested,
        message="Just created",
        last_updated_epoch_seconds=time.time(),
    )
    job = make_job(
        name="foo",
        namespace="bar",
        run_id="abc123",
        status=status,
        details=JobDetails(try_number=0),
        kind=JobKind.run,
    )
    assert len(job.status_history) == 1

    new_status = replace(
        status, last_updated_epoch_seconds=status.last_updated_epoch_seconds + 1
    )
    job.update_status(new_status)

    assert job.message == new_status.message
    assert job.state == new_status.state
    assert job.last_updated_epoch_seconds == new_status.last_updated_epoch_seconds

    # new status is the same as the old except for timestamp.
    assert len(job.status_history) == 1

    new_status = replace(
        new_status,
        last_updated_epoch_seconds=new_status.last_updated_epoch_seconds + 1,
        state=KubernetesJobState.Running,
    )
    job.update_status(new_status)

    assert job.message == new_status.message
    assert job.state == new_status.state
    assert job.last_updated_epoch_seconds == new_status.last_updated_epoch_seconds

    job.status_history == (new_status, status)


def test_update_with_out_of_order_status():
    status = JobStatus(
        state=KubernetesJobState.Requested,
        message="Just created",
        last_updated_epoch_seconds=time.time(),
    )
    job = make_job(
        name="foo",
        namespace="bar",
        run_id="abc123",
        status=status,
        details=JobDetails(try_number=0),
        kind=JobKind.run,
    )
    older_status = replace(
        status, last_updated_epoch_seconds=status.last_updated_epoch_seconds - 1
    )

    with pytest.raises(IllegalStateTransitionError):
        job.update_status(older_status)


def test_update_reanimate_dead_job():
    status = JobStatus(
        state=KubernetesJobState.Requested,
        message="Just created",
        last_updated_epoch_seconds=time.time(),
    )
    job = make_job(
        name="foo",
        namespace="bar",
        run_id="abc123",
        status=status,
        details=JobDetails(try_number=0),
        kind=JobKind.run,
    )
    failed_status = JobStatus(
        last_updated_epoch_seconds=status.last_updated_epoch_seconds + 1,
        message="Oh no!",
        state=KubernetesJobState.Failed,
    )

    job.update_status(failed_status)

    running_again_status = JobStatus(
        last_updated_epoch_seconds=failed_status.last_updated_epoch_seconds + 1,
        message="Had a run in with Dr. Frankenstein...",
        state=KubernetesJobState.Running,
    )
    with pytest.raises(IllegalStateTransitionError):
        job.update_status(running_again_status)
