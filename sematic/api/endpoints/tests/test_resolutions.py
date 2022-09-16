# Standard Library
import typing
from unittest import mock

# Third-party
import flask.testing
import pytest

# Sematic
from sematic.api.tests.fixtures import (  # noqa: F401
    make_auth_test,
    mock_no_auth,
    mock_requests,
    test_client,
)
from sematic.db.models.resolution import Resolution, ResolutionStatus
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
