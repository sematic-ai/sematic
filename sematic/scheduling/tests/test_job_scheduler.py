# Standard Library
import time
from unittest import mock

# Third-party
import pytest

# Sematic
from sematic.abstract_future import FutureState
from sematic.db.models.git_info import GitInfo
from sematic.db.models.job import Job
from sematic.db.models.resolution import Resolution, ResolutionKind, ResolutionStatus
from sematic.db.models.run import Run
from sematic.db.tests.fixtures import make_job
from sematic.resolvers.resource_requirements import (
    KubernetesResourceRequirements,
    ResourceRequirements,
)
from sematic.scheduling.job_details import JobStatus, KubernetesJobState
from sematic.scheduling.job_scheduler import (
    StateNotSchedulable,
    _refresh_jobs,
    schedule_resolution,
    schedule_run,
)
from sematic.versions import CURRENT_VERSION_STR


@pytest.fixture
def mock_k8s():
    with mock.patch("sematic.scheduling.job_scheduler.k8s") as mock_k8s:
        mock_k8s.schedule_run_job.side_effect = lambda *_, **__: make_job(name="job1")
        mock_k8s.schedule_resolution_job.side_effect = lambda *_, **__: make_job(
            name="job2"
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
        client_version=CURRENT_VERSION_STR,
    )


def test_schedule_run(mock_k8s, run: Run, resolution: Resolution):
    resolution.status = ResolutionStatus.RUNNING
    run.container_image_uri = resolution.container_image_uri
    _, jobs = schedule_run(run, resolution, [])
    assert len(jobs) == 1
    job = jobs[0]
    assert isinstance(job, Job)
    assert job.details.get_status(time.time()).state == "Requested"
    assert job.latest_status.state == "Requested"

    mock_k8s.schedule_run_job.assert_called_once()
    mock_k8s.schedule_run_job.assert_called_with(
        run_id=run.id,
        image=resolution.container_image_uri,
        user_settings=resolution.settings_env_vars,
        resource_requirements=run.resource_requirements,
        try_number=0,
    )


def test_schedule_resolution(mock_k8s, resolution: Resolution):
    _, job = schedule_resolution(resolution, max_parallelism=3, rerun_from="foobar")
    assert isinstance(job, Job)
    mock_k8s.schedule_resolution_job.assert_called_once()
    mock_k8s.schedule_resolution_job.assert_called_with(
        resolution_id=resolution.root_id,
        image=resolution.container_image_uri,
        user_settings=resolution.settings_env_vars,
        max_parallelism=3,
        rerun_from="foobar",
    )


def test_schedule_resolution_bad_version(mock_k8s, resolution: Resolution):
    resolution.client_version = "0.0.0"
    with pytest.raises(StateNotSchedulable, match=r".*0\.0\.0\.*"):
        schedule_resolution(resolution, max_parallelism=3, rerun_from="foobar")
    mock_k8s.schedule_resolution_job.assert_not_called()


def test_refresh_jobs(mock_k8s):
    job1 = make_job(name="job1")
    job2 = make_job(name="job2")
    refreshed = _refresh_jobs([job1, job2])
    assert [job.identifier() for job in refreshed] == [
        job1.identifier(),
        job2.identifier(),
    ]
    assert mock_k8s.refresh_job.call_count == 2

    mock_k8s.refresh_job.reset_mock()

    job2.update_status(
        JobStatus(
            state=KubernetesJobState.Failed,
            message="failed",
            last_updated_epoch_seconds=time.time(),
        )
    )
    refreshed = _refresh_jobs([job1, job2])
    assert [job.identifier() for job in refreshed] == [
        job1.identifier(),
        job2.identifier(),
    ]
    assert mock_k8s.refresh_job.call_count == 1
