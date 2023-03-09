# Standard Library
from dataclasses import replace

# Third-party
import pytest

# Sematic
from sematic.db.models.job import Job
from sematic.scheduling.external_job import JobType
from sematic.scheduling.kubernetes import KubernetesExternalJob
from sematic.utils.exceptions import IllegalStateTransitionError


def test_from_job():
    run_id = "abc123"
    namespace = "fakens"
    k8s_job = KubernetesExternalJob.new(
        try_number=0,
        run_id=run_id,
        namespace=namespace,
        job_type=JobType.worker,
    )
    job = Job.from_job(k8s_job, run_id=run_id)
    assert job.id == k8s_job.external_job_id
    assert job.is_active
    assert job.job_type == JobType.worker
    assert job.source_run_id == run_id
    assert job.state_name == k8s_job.get_status().state_name
    assert job.status_message == k8s_job.get_status().description
    assert job.last_updated_epoch_seconds == k8s_job.epoch_time_last_updated

    assert job.job == k8s_job


def test_set_job():
    run_id = "abc123"
    namespace = "fakens"
    k8s_job = KubernetesExternalJob.new(
        try_number=0,
        run_id=run_id,
        namespace=namespace,
        job_type=JobType.worker,
    )
    job = Job.from_job(k8s_job, run_id=run_id)
    updated_k8s_job = replace(
        k8s_job,
        has_started=True,
        epoch_time_last_updated=k8s_job.epoch_time_last_updated + 1,
    )
    job.set_job(updated_k8s_job)
    assert len(job.status_history) == 2
    assert job.status_history[0] == updated_k8s_job.get_status()
    assert job.status_history[1] == k8s_job.get_status()

    assert job.job == updated_k8s_job


def test_illegal_set_job():
    run_id = "abc123"
    namespace = "fakens"
    k8s_job = KubernetesExternalJob.new(
        try_number=0,
        run_id=run_id,
        namespace=namespace,
        job_type=JobType.worker,
    )
    job = Job.from_job(k8s_job, run_id=run_id)
    updated_k8s_job = replace(
        k8s_job,
        has_started=True,
        epoch_time_last_updated=k8s_job.epoch_time_last_updated - 1,
    )

    with pytest.raises(IllegalStateTransitionError):
        job.set_job(updated_k8s_job)

    assert job.job == k8s_job
    assert len(job.status_history) == 1

    updated_k8s_job = replace(
        k8s_job,
        external_job_id="foo",
    )

    with pytest.raises(ValueError):
        job.set_job(updated_k8s_job)

    assert job.job == k8s_job
    assert len(job.status_history) == 1

    updated_k8s_job = replace(
        k8s_job,
        has_started=True,
        still_exists=False,
    )

    job.set_job(updated_k8s_job)

    assert job.job == updated_k8s_job
    assert len(job.status_history) == 2

    with pytest.raises(IllegalStateTransitionError):
        job.set_job(k8s_job)
