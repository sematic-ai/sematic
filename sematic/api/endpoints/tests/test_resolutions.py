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
    mock_auth,
    mock_requests,
    test_client,
)
from sematic.db.models.resolution import Resolution, ResolutionStatus
from sematic.db.models.run import Run
from sematic.db.queries import (
    get_graph,
    get_resolution,
    get_run,
    save_resolution,
    save_run,
    save_run_external_resource_links,
)
from sematic.db.tests.fixtures import (  # noqa: F401
    make_resolution,
    persisted_external_resource,
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
test_cancel_resolution_auth = make_auth_test(
    "/api/v1/resolutions/123/cancel", method="PUT"
)
test_rerun_resolution_auth = make_auth_test(
    "/api/v1/resolutions/123/rerun", method="POST"
)
test_list_external_resource_auth = make_auth_test(
    "/api/v1/resolutions/123/external_resources", method="GET"
)


def mock_schedule(
    resolution,  # noqa: F811
    cache_namespace=None,
    max_parallelism=None,
    rerun_from=None,
):
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


@pytest.fixture
def mock_schedule_resolution():
    with mock.patch(
        "sematic.api.endpoints.resolutions.schedule_resolution",
        side_effect=mock_schedule,
    ) as mock_schedule_resolution_:
        yield mock_schedule_resolution_


def test_get_resolution_endpoint(
    mock_auth,  # noqa: F811
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


def test_put_resolution_endpoint(
    mock_auth,  # noqa: F811
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


def test_get_resolution_404(
    mock_auth, test_client: flask.testing.FlaskClient  # noqa: F811
):
    response = test_client.get("/api/v1/resolutions/unknownid")

    assert response.status_code == 404

    payload = response.json
    payload = typing.cast(typing.Dict[str, typing.Any], payload)

    assert payload == dict(error="No resolutions with id 'unknownid'")


def test_schedule_resolution_endpoint(
    mock_auth,  # noqa: F811
    persisted_resolution: Resolution,  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811
    mock_schedule_resolution: mock.MagicMock,
):
    response = test_client.post(
        "/api/v1/resolutions/{}/schedule".format(persisted_resolution.root_id),
        json={"max_parallelism": 3, "rerun_from": "rerun_from_run_id"},
    )

    payload = response.json
    payload = typing.cast(typing.Dict[str, typing.Any], payload)

    assert payload["content"]["root_id"] == persisted_resolution.root_id
    assert len(payload["content"]["external_jobs_json"]) == 1
    mock_schedule_resolution.assert_called_once()
    scheduled_resolution = mock_schedule_resolution.call_args.kwargs["resolution"]
    assert isinstance(scheduled_resolution, Resolution)
    assert scheduled_resolution.root_id == persisted_resolution.root_id
    assert mock_schedule_resolution.call_args.kwargs["max_parallelism"] == 3
    assert (
        mock_schedule_resolution.call_args.kwargs["rerun_from"] == "rerun_from_run_id"
    )


@mock.patch("sematic.api.endpoints.resolutions.cancel_job")
def test_cancel_resolution(
    mock_cancel_job: mock.MagicMock,
    persisted_resolution: Resolution,  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811
    test_db,  # noqa: F811
    mock_auth,  # noqa: F811
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


def test_rerun_resolution_endpoint(
    persisted_resolution: Resolution,  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811
    test_db,  # noqa: F811
    mock_auth,  # noqa: F811
    mock_schedule_resolution: mock.MagicMock,
):
    response = test_client.post(
        f"/api/v1/resolutions/{persisted_resolution.root_id}/rerun",
        json={"rerun_from": persisted_resolution.root_id},
    )

    assert response.status_code == 200

    payload = response.json
    payload = typing.cast(typing.Dict[str, typing.Any], payload)

    cloned_resolution = get_resolution(payload["content"]["root_id"])

    assert cloned_resolution.status == ResolutionStatus.SCHEDULED.value

    run = get_run(cloned_resolution.root_id)  # noqa: F811

    assert run.parent_id is None
    assert run.future_state == FutureState.CREATED.value

    mock_schedule_resolution.assert_called_once()
    mock_schedule_resolution.call_args.kwargs[
        "rerun_from"
    ] == persisted_resolution.root_id


def test_list_external_resources_empty(
    mock_auth, test_client: flask.testing.FlaskClient  # noqa: F811
):
    response = test_client.get("/api/v1/resolutions/abc123/external_resources")
    assert response.status_code == 200

    assert response.json == dict(external_resources=[])


def test_list_external_resource_ids(
    mock_auth,  # noqa: F811
    persisted_run,  # noqa: F811
    persisted_external_resource,  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811
):
    save_run_external_resource_links([persisted_external_resource.id], persisted_run.id)
    response = test_client.get(
        f"/api/v1/resolutions/{persisted_run.id}/external_resources"
    )
    assert response.status_code == 200

    result_ids = [
        resource["id"]
        for resource in response.json["external_resources"]  # type: ignore
    ]
    assert result_ids == [persisted_external_resource.id]
