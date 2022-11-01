# Standard Library
from unittest import mock

# Third-party
import pytest

# Sematic
from sematic.abstract_future import FutureState
from sematic.db.models.git_info import GitInfo
from sematic.db.models.resolution import Resolution, ResolutionKind, ResolutionStatus
from sematic.db.models.run import Run
from sematic.resolvers.resource_requirements import (
    KubernetesResourceRequirements,
    ResourceRequirements,
)
from sematic.scheduling.external_job import JobType
from sematic.scheduling.job_scheduler import (
    _refresh_external_jobs,
    schedule_resolution,
    schedule_run,
)
from sematic.scheduling.kubernetes import KubernetesExternalJob


@pytest.fixture
def mock_k8s():
    with mock.patch("sematic.scheduling.job_scheduler.k8s") as mock_k8s:
        mock_k8s.schedule_run_job.side_effect = (
            lambda *_, **__: KubernetesExternalJob.new(
                try_number=0, run_id="aaa", namespace="foo", job_type=JobType.worker
            )
        )
        mock_k8s.schedule_resolution_job.side_effect = (
            lambda *_, **__: KubernetesExternalJob.new(
                try_number=0, run_id="aaa", namespace="foo", job_type=JobType.driver
            )
        )
        mock_k8s.refresh_job.side_effect = lambda job: job
        yield mock_k8s


@pytest.fixture
def run():
    run_id = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    run = Run(
        id=run_id,
        calculator_path="foo.bar",
        root_id=run_id,
        future_state=FutureState.CREATED,
    )
    run.resource_requirements = ResourceRequirements(
        kubernetes=KubernetesResourceRequirements(
            requests={"cpu": "42"},
        )
    )
    yield run


@pytest.fixture
def resolution(run):
    yield Resolution(
        root_id=run.id,
        status=ResolutionStatus.CREATED,
        kind=ResolutionKind.KUBERNETES,
        container_image_uri="my.uri",
        container_image_uris={"default": "my.uri"},
        git_info=GitInfo(
            remote="remote", branch="branch", commit="commit", dirty=False
        ),
        settings_env_vars={"SOME_ENV_VAR": "some_value"},
    )


def test_schedule_run(mock_k8s, run: Run, resolution: Resolution):
    resolution.status = ResolutionStatus.RUNNING
    run.container_image_uri = resolution.container_image_uri
    scheduled = schedule_run(run, resolution)
    assert len(scheduled.external_jobs) == 1
    external_job = scheduled.external_jobs[0]
    assert isinstance(external_job, KubernetesExternalJob)
    mock_k8s.schedule_run_job.assert_called_once()
    mock_k8s.schedule_run_job.assert_called_with(
        run_id=run.id,
        image=resolution.container_image_uri,
        user_settings=resolution.settings_env_vars,
        resource_requirements=run.resource_requirements,
        try_number=0,
    )


def test_schedule_resolution(mock_k8s, resolution: Resolution):
    scheduled = schedule_resolution(resolution, max_parallelism=3, rerun_from="foobar")
    assert len(scheduled.external_jobs) == 1
    external_job = scheduled.external_jobs[0]
    assert isinstance(external_job, KubernetesExternalJob)
    mock_k8s.schedule_resolution_job.assert_called_once()
    mock_k8s.schedule_resolution_job.assert_called_with(
        resolution_id=resolution.root_id,
        image=resolution.container_image_uri,
        user_settings=resolution.settings_env_vars,
        max_parallelism=3,
        rerun_from="foobar",
    )


def test_refresh_external_jobs(mock_k8s):
    job1 = KubernetesExternalJob.new(
        try_number=0, run_id="aaa", namespace="foo", job_type=JobType.worker
    )
    job2 = KubernetesExternalJob.new(
        try_number=0, run_id="bbb", namespace="foo", job_type=JobType.worker
    )
    refreshed = _refresh_external_jobs([job1, job2])
    assert [job.external_job_id for job in refreshed] == [
        job1.external_job_id,
        job2.external_job_id,
    ]
    assert mock_k8s.refresh_job.call_count == 2

    mock_k8s.refresh_job.reset_mock()

    job2.is_active = lambda: False
    refreshed = _refresh_external_jobs([job1, job2])
    assert [job.external_job_id for job in refreshed] == [
        job1.external_job_id,
        job2.external_job_id,
    ]
    assert mock_k8s.refresh_job.call_count == 1
