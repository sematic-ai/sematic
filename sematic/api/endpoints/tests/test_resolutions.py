# Standard Library
import typing
from unittest import mock

# Third-party
import flask.testing
import pytest

# Sematic
from sematic.abstract_future import FutureState
from sematic.api.tests.fixtures import (  # noqa: F401
    make_auth_test,
    mock_no_auth,
    mock_requests,
    test_client,
)
from sematic.db.models.resolution import Resolution, ResolutionStatus
from sematic.db.models.run import Run
from sematic.db.queries import get_graph, get_resolution, save_resolution, save_run
from sematic.db.tests.fixtures import (  # noqa: F401
    make_resolution,
    persisted_resolution,
    persisted_run,
    pg_mock,
    resolution,
    run,
    test_db,
)
from sematic.scheduling.external_job import JobType
from sematic.scheduling.kubernetes import KubernetesExternalJob

test_get_resolution_auth = make_auth_test("/api/v1/resolutions/123")
test_put_resolution_auth = make_auth_test("/api/v1/resolutions/123", method="PUT")
test_schedule_resolution_auth = make_auth_test(
    "/api/v1/resolutions/123/schedule", method="POST"
)


@pytest.fixture
def mock_schedule_resolution():
    with mock.patch(
        "sematic.api.endpoints.resolutions.schedule_resolution"
    ) as mock_schedule:
        yield mock_schedule


@mock_no_auth
def test_get_resolution_endpoint(
    persisted_resolution: Resolution,  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811
):
    response = test_client.get(
        "/api/v1/resolutions/{}".format(persisted_resolution.root_id)
    )

    payload = response.json
    payload = typing.cast(typing.Dict[str, typing.Any], payload)

    assert payload["content"]["root_id"] == persisted_resolution.root_id

    # Should have been scrubbed
    assert payload["content"]["settings_env_vars"] == {}


@mock_no_auth
def test_put_resolution_endpoint(
    persisted_run,  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811
):
    resolution = make_resolution(root_id=persisted_run.id)  # noqa: F811
    response = test_client.put(
        "/api/v1/resolutions/{}".format(resolution.root_id),
        json={"resolution": resolution.to_json_encodable()},
    )
    response = test_client.get("/api/v1/resolutions/{}".format(resolution.root_id))
    encodable = response.json["content"]  # type: ignore
    encodable["status"] = ResolutionStatus.FAILED.value

    test_client.put(
        "/api/v1/resolutions/{}".format(resolution.root_id),
        json={"resolution": encodable},
    )

    read = get_resolution(resolution.root_id)
    assert read.settings_env_vars == resolution.settings_env_vars
    assert read.status == ResolutionStatus.FAILED.value


@mock_no_auth
def test_get_resolution_404(test_client: flask.testing.FlaskClient):  # noqa: F811
    response = test_client.get("/api/v1/resolutions/unknownid")

    assert response.status_code == 404

    payload = response.json
    payload = typing.cast(typing.Dict[str, typing.Any], payload)

    assert payload == dict(error="No resolutions with id 'unknownid'")


@mock_no_auth
def test_schedule_resolution_endpoint(
    persisted_resolution: Resolution,  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811
    mock_schedule_resolution: mock.MagicMock,
):
    def mock_schedule(resolution):  # noqa: F811
        resolution.status = ResolutionStatus.SCHEDULED
        resolution.external_jobs = (
            KubernetesExternalJob.new(
                try_number=0,
                run_id="a",
                namespace="foo",
                job_type=JobType.driver,
            ),
        )
        return resolution

    mock_schedule_resolution.side_effect = mock_schedule
    response = test_client.post(
        "/api/v1/resolutions/{}/schedule".format(persisted_resolution.root_id)
    )

    payload = response.json
    payload = typing.cast(typing.Dict[str, typing.Any], payload)

    assert payload["content"]["root_id"] == persisted_resolution.root_id
    assert len(payload["content"]["external_jobs_json"]) == 1
    mock_schedule_resolution.assert_called_once()
    scheduled_resolution = mock_schedule_resolution.call_args[0][0]
    assert isinstance(scheduled_resolution, Resolution)
    assert scheduled_resolution.root_id == persisted_resolution.root_id


@mock.patch("sematic.api.endpoints.resolutions.cancel_job")
@mock_no_auth
def test_cancel_resolution(
    mock_cancel_job: mock.MagicMock,
    persisted_resolution: Resolution,  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811
    test_db,  # noqa: F811
):
    persisted_resolution.external_jobs = (
        KubernetesExternalJob.new(
            try_number=0,
            run_id="a",
            namespace="foo",
            job_type=JobType.driver,
        ),
    )
    save_resolution(persisted_resolution)

    runs, _, __ = get_graph(
        Run.root_id == persisted_resolution.root_id,
        include_artifacts=False,
        include_edges=False,
    )
    runs[0].external_jobs = (
        KubernetesExternalJob.new(
            try_number=0,
            run_id="a",
            namespace="foo",
            job_type=JobType.worker,
        ),
    )
    save_run(runs[0])

    response = test_client.put(
        f"/api/v1/resolutions/{persisted_resolution.root_id}/cancel"
    )

    assert response.status_code == 200

    canceled_resolution = get_resolution(persisted_resolution.root_id)

    assert canceled_resolution.status == ResolutionStatus.CANCELED.value

    runs, _, __ = get_graph(
        Run.root_id == canceled_resolution.root_id,
        include_artifacts=False,
        include_edges=False,
    )

    for canceled_run in runs:
        assert canceled_run.future_state == FutureState.CANCELED.value

    assert mock_cancel_job.call_count == 2
