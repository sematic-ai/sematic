# Standard Library
import time
import typing
from copy import copy
from dataclasses import replace
from http import HTTPStatus
from unittest import mock

# Third-party
import flask.testing
import pytest

# Sematic
from sematic.abstract_future import FutureState
from sematic.abstract_plugin import (
    SEMATIC_PLUGIN_AUTHOR,
    AbstractPlugin,
    PluginScope,
    PluginVersion,
)
from sematic.api.tests.fixtures import (  # noqa: F401
    make_auth_test,
    mock_auth,
    mock_requests,
    test_client,
    with_auth,
)
from sematic.config.user_settings import UserSettingsVar
from sematic.db.models.resolution import Resolution, ResolutionStatus
from sematic.db.models.run import Run
from sematic.db.models.user import User
from sematic.db.queries import (
    count_jobs_by_run_id,
    get_graph,
    get_jobs_by_run_id,
    get_resolution,
    get_run,
    save_job,
    save_resolution,
    save_run_external_resource_links,
)
from sematic.db.tests.fixtures import (  # noqa: F401
    allow_any_run_state_transition,
    make_job,
    make_resolution,
    other_persisted_user,
    persisted_external_resource,
    persisted_resolution,
    persisted_resolution_w_user,
    persisted_run,
    persisted_run_w_user,
    persisted_user,
    pg_mock,
    resolution,
    run,
    test_db,
)
from sematic.plugins.abstract_publisher import AbstractPublisher
from sematic.scheduling.job_details import JobKind
from sematic.tests.fixtures import environment_variables

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


class MockPublisher(AbstractPublisher, AbstractPlugin):
    # can't use assert_called* on a mock because the class is independently
    # re-instantiated on every resolution publish event
    call_counter = 0

    @staticmethod
    def get_author() -> str:
        return SEMATIC_PLUGIN_AUTHOR

    @staticmethod
    def get_version() -> PluginVersion:
        return 0, 1, 0

    def publish(self, event: typing.Any) -> None:
        MockPublisher.call_counter += 1


def mock_schedule(resolution, max_parallelism=None, rerun_from=None):  # noqa: F811
    resolution.status = ResolutionStatus.SCHEDULED
    job = make_job(run_id=resolution.root_id, kind="resolver")
    save_job(job)
    return resolution, job


@pytest.fixture
def mock_schedule_resolution():
    with mock.patch(
        "sematic.api.endpoints.resolutions.schedule_resolution",
        side_effect=mock_schedule,
    ) as mock_schedule_resolution_:
        yield mock_schedule_resolution_


@pytest.fixture
def mock_schedule_kubernetes():
    with mock.patch(
        "sematic.scheduling.job_scheduler.k8s",
        side_effect=mock_schedule,
    ) as mock_scheduler_k8s:
        yield mock_scheduler_k8s


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


def test_put_resolution_endpoint_no_auth(
    mock_auth,  # noqa: F811
    persisted_run,  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811
):
    resolution = make_resolution(root_id=persisted_run.id)  # noqa: F811
    response = test_client.put(
        "/api/v1/resolutions/{}".format(resolution.root_id),
        json={"resolution": resolution.to_json_encodable(redact=False)},
    )

    assert response.status_code == HTTPStatus.OK

    response = test_client.get("/api/v1/resolutions/{}".format(resolution.root_id))

    assert response.status_code == HTTPStatus.OK

    encodable = response.json["content"]  # type: ignore

    assert encodable["settings_env_vars"] == {}

    read = get_resolution(resolution.root_id)
    assert read.settings_env_vars == resolution.settings_env_vars
    assert read.status == ResolutionStatus.SCHEDULED.value
    assert read.user_id is None

    encodable["status"] = ResolutionStatus.COMPLETE.value
    response = test_client.put(
        "/api/v1/resolutions/{}".format(resolution.root_id),
        json={"resolution": encodable},
    )

    # check an incorrect transition was ignored
    assert response.status_code == HTTPStatus.BAD_REQUEST
    read = get_resolution(resolution.root_id)
    assert read.status == ResolutionStatus.SCHEDULED.value
    assert read.user_id is None

    encodable["status"] = ResolutionStatus.RUNNING.value
    response = test_client.put(
        "/api/v1/resolutions/{}".format(resolution.root_id),
        json={"resolution": encodable},
    )

    # check the resolution was updated
    assert response.status_code == HTTPStatus.OK
    read = get_resolution(resolution.root_id)
    assert read.status == ResolutionStatus.RUNNING.value
    assert read.user_id is None


def test_put_resolution_endpoint_auth(
    with_auth,  # noqa: F811
    persisted_run_w_user,  # noqa: F811
    persisted_user,  # noqa: F811
    other_persisted_user,  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811
):
    resolution = make_resolution(root_id=persisted_run_w_user.id)  # noqa: F811
    expected_env_vars = _get_expected_env_vars(resolution, persisted_user)

    # check the resolution creation succeeds:
    response = test_client.put(
        "/api/v1/resolutions/{}".format(resolution.root_id),
        json={"resolution": resolution.to_json_encodable(redact=False)},
        headers=({"X-API-KEY": persisted_user.api_key}),
    )

    assert response.status_code == HTTPStatus.OK

    response = test_client.get(
        "/api/v1/resolutions/{}".format(resolution.root_id),
        headers=({"X-API-KEY": persisted_user.api_key}),
    )

    assert response.status_code == HTTPStatus.OK

    encodable = response.json["content"]  # type: ignore

    assert encodable["settings_env_vars"] == {}

    read = get_resolution(resolution.root_id)

    assert read.settings_env_vars == expected_env_vars
    assert read.status == ResolutionStatus.SCHEDULED.value
    assert read.user_id == persisted_user.id

    # check an incorrect transition fails:
    encodable["status"] = ResolutionStatus.COMPLETE.value
    response = test_client.put(
        "/api/v1/resolutions/{}".format(resolution.root_id),
        json={"resolution": encodable},
        headers=({"X-API-KEY": persisted_user.api_key}),
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    read = get_resolution(resolution.root_id)
    assert read.settings_env_vars == expected_env_vars
    assert read.status == ResolutionStatus.SCHEDULED.value
    assert read.user_id == persisted_user.id

    # check a correct transition succeeds:
    encodable["status"] = ResolutionStatus.RUNNING.value
    response = test_client.put(
        "/api/v1/resolutions/{}".format(resolution.root_id),
        json={"resolution": encodable},
        headers=({"X-API-KEY": persisted_user.api_key}),
    )

    assert response.status_code == HTTPStatus.OK
    read = get_resolution(resolution.root_id)
    assert read.settings_env_vars == expected_env_vars
    assert read.status == ResolutionStatus.RUNNING.value
    assert read.user_id == persisted_user.id

    # check updating an immutable field fails:
    encodable["status"] = ResolutionStatus.COMPLETE.value
    response = test_client.put(
        "/api/v1/resolutions/{}".format(resolution.root_id),
        json={"resolution": encodable},
        headers=({"X-API-KEY": other_persisted_user.api_key}),
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    read = get_resolution(resolution.root_id)
    assert read.settings_env_vars == expected_env_vars
    assert read.status == ResolutionStatus.RUNNING.value
    assert read.user_id == persisted_user.id


def test_resolution_event_publishing(
    mock_auth,  # noqa: F811
    persisted_run,  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811,
):
    resolution = make_resolution(  # noqa: F811
        root_id=persisted_run.id, status=ResolutionStatus.FAILED
    )

    with environment_variables({PluginScope.PUBLISH.value: MockPublisher.get_path()}):
        assert MockPublisher.call_counter == 0

        response = test_client.put(
            "/api/v1/resolutions/{}".format(resolution.root_id),
            json={"resolution": resolution.to_json_encodable()},
        )

        assert response.status_code == HTTPStatus.OK
        assert MockPublisher.call_counter == 1


def test_get_resolution_404(
    mock_auth, test_client: flask.testing.FlaskClient  # noqa: F811
):
    response = test_client.get("/api/v1/resolutions/unknownid")

    assert response.status_code == HTTPStatus.NOT_FOUND

    payload = response.json
    payload = typing.cast(typing.Dict[str, typing.Any], payload)

    assert payload == dict(error="No resolutions with id 'unknownid'")


def test_schedule_resolution_endpoint_no_auth(
    mock_auth,  # noqa: F811
    persisted_resolution: Resolution,  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811
    mock_schedule_resolution: mock.MagicMock,
):
    response = test_client.post(
        "/api/v1/resolutions/{}/schedule".format(persisted_resolution.root_id),
        json={"max_parallelism": 3, "rerun_from": "rerun_from_run_id"},
    )

    assert response.status_code == HTTPStatus.OK

    payload = typing.cast(typing.Dict[str, typing.Any], response.json)

    assert payload["content"]["root_id"] == persisted_resolution.root_id
    assert count_jobs_by_run_id(persisted_resolution.root_id, "resolver") == 1
    assert payload["content"]["user_id"] is None
    assert payload["content"]["settings_env_vars"] == {}
    mock_schedule_resolution.assert_called_once()

    scheduled_resolution = mock_schedule_resolution.call_args.kwargs["resolution"]
    assert isinstance(scheduled_resolution, Resolution)
    assert scheduled_resolution.root_id == persisted_resolution.root_id
    assert mock_schedule_resolution.call_args.kwargs["max_parallelism"] == 3
    assert (
        mock_schedule_resolution.call_args.kwargs["rerun_from"] == "rerun_from_run_id"
    )


def test_clean_resolution_jobs(
    mock_auth,  # noqa: F811
    persisted_resolution: Resolution,  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811
    mock_schedule_kubernetes: mock.MagicMock,
):
    def mock_cancel_job(job):
        details = job.details
        details.canceled = True
        job.details = details
        job.update_status(details.get_status(job.last_updated_epoch_seconds + 1))
        return job

    mock_schedule_kubernetes.cancel_job = mock_cancel_job

    job = make_job(run_id=persisted_resolution.root_id, kind=JobKind.resolver)
    save_job(job)
    response = test_client.post(
        f"/api/v1/resolutions/{persisted_resolution.root_id}/clean_jobs",
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST

    persisted_resolution.status = ResolutionStatus.FAILED
    save_resolution(persisted_resolution)
    response = test_client.post(
        f"/api/v1/resolutions/{persisted_resolution.root_id}/clean_jobs",
    )
    assert response.status_code == HTTPStatus.OK

    payload = typing.cast(typing.Dict[str, typing.Any], response.json)

    assert payload["content"] == ["DELETED"]


def test_schedule_resolution_endpoint_auth(
    with_auth,  # noqa: F811
    persisted_resolution: Resolution,  # noqa: F811
    persisted_user,  # noqa: F811
    other_persisted_user,  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811
    mock_schedule_resolution: mock.MagicMock,
):
    response = test_client.post(
        "/api/v1/resolutions/{}/schedule".format(persisted_resolution.root_id),
        json={"max_parallelism": 3, "rerun_from": "rerun_from_run_id"},
        headers=({"X-API-KEY": persisted_user.api_key}),
    )

    assert response.status_code == HTTPStatus.OK

    payload = typing.cast(typing.Dict[str, typing.Any], response.json)

    assert payload["content"]["root_id"] == persisted_resolution.root_id
    assert count_jobs_by_run_id(persisted_resolution.root_id, "resolver") == 1
    assert payload["content"]["user_id"] == persisted_user.id
    assert payload["content"]["settings_env_vars"] == {}
    mock_schedule_resolution.assert_called_once()

    scheduled_resolution = mock_schedule_resolution.call_args.kwargs["resolution"]
    assert isinstance(scheduled_resolution, Resolution)
    assert scheduled_resolution.root_id == persisted_resolution.root_id
    assert mock_schedule_resolution.call_args.kwargs["max_parallelism"] == 3
    assert (
        mock_schedule_resolution.call_args.kwargs["rerun_from"] == "rerun_from_run_id"
    )


@mock.patch("sematic.api.endpoints.resolutions.broadcast_resolution_cancel")
@mock.patch("sematic.api.endpoints.resolutions.broadcast_graph_update")
@mock.patch("sematic.api.endpoints.resolutions.cancel_job")
def test_cancel_resolution(
    mock_cancel_job: mock.MagicMock,
    mock_broadcast_update: mock.MagicMock,
    mock_broadcast_cancel: mock.MagicMock,
    persisted_resolution: Resolution,  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811
    test_db,  # noqa: F811
    mock_auth,  # noqa: F811
):
    def fake_cancel(job):
        details = job.details
        details = replace(details, still_exists=False, has_started=True)
        job.details = details
        job.update_status(details.get_status(time.time()))
        return job

    mock_cancel_job.side_effect = fake_cancel

    job = make_job(run_id=persisted_resolution.root_id, kind="resolver")
    save_job(job)
    save_resolution(persisted_resolution)

    runs, _, __ = get_graph(
        Run.root_id == persisted_resolution.root_id,
        include_artifacts=False,
        include_edges=False,
    )

    run_job = make_job(run_id=runs[0].id, kind="run", name="run-job")
    save_job(run_job)

    response = test_client.put(
        f"/api/v1/resolutions/{persisted_resolution.root_id}/cancel"
    )

    assert response.status_code == HTTPStatus.OK
    mock_broadcast_update.assert_called()
    mock_broadcast_cancel.assert_called()

    canceled_resolution = get_resolution(persisted_resolution.root_id)
    for job in get_jobs_by_run_id(canceled_resolution.root_id, "resolver"):
        assert not job.latest_status.is_active()

    assert canceled_resolution.status == ResolutionStatus.CANCELED.value

    runs, _, __ = get_graph(
        Run.root_id == canceled_resolution.root_id,
        include_artifacts=False,
        include_edges=False,
    )

    for canceled_run in runs:
        assert canceled_run.future_state == FutureState.CANCELED.value

    assert mock_cancel_job.call_count == 2

    # double tap
    response = test_client.put(
        f"/api/v1/resolutions/{persisted_resolution.root_id}/cancel"
    )

    assert response.status_code == HTTPStatus.OK
    assert mock_broadcast_update.call_count == 1
    assert mock_broadcast_cancel.call_count == 1

    canceled_resolution = get_resolution(persisted_resolution.root_id)
    assert canceled_resolution.status == ResolutionStatus.CANCELED.value


@mock.patch("sematic.api.endpoints.resolutions.broadcast_pipeline_update")
def test_rerun_resolution_endpoint_no_auth(
    mock_broadcast_update: mock.MagicMock,
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
    mock_broadcast_update.assert_called()

    assert response.status_code == HTTPStatus.OK

    payload = response.json
    payload = typing.cast(typing.Dict[str, typing.Any], payload)

    cloned_resolution = get_resolution(payload["content"]["root_id"])

    assert cloned_resolution.status == ResolutionStatus.SCHEDULED.value
    assert cloned_resolution.user_id is None

    run = get_run(cloned_resolution.root_id)  # noqa: F811

    assert run.parent_id is None
    assert run.future_state == FutureState.CREATED.value
    assert run.user_id is None

    mock_schedule_resolution.assert_called_once()
    assert (
        mock_schedule_resolution.call_args.kwargs["rerun_from"]
        == persisted_resolution.root_id
    )


@mock.patch("sematic.api.endpoints.resolutions.broadcast_pipeline_update")
def test_rerun_resolution_endpoint_auth_same_user(
    mock_broadcast_update: mock.MagicMock,
    persisted_resolution_w_user: Resolution,  # noqa: F811
    persisted_user: User,  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811
    test_db,  # noqa: F811
    with_auth,  # noqa: F811
    mock_schedule_resolution: mock.MagicMock,
):
    response = test_client.post(
        f"/api/v1/resolutions/{persisted_resolution_w_user.root_id}/rerun",
        json={"rerun_from": persisted_resolution_w_user.root_id},
        headers=({"X-API-KEY": persisted_user.api_key}),
    )

    assert response.status_code == HTTPStatus.OK
    mock_broadcast_update.assert_called()

    payload = response.json
    payload = typing.cast(typing.Dict[str, typing.Any], payload)

    cloned_resolution = get_resolution(payload["content"]["root_id"])

    assert cloned_resolution.status == ResolutionStatus.SCHEDULED.value
    assert cloned_resolution.user_id == persisted_user.id

    run = get_run(cloned_resolution.root_id)  # noqa: F811

    assert run.parent_id is None
    assert run.future_state == FutureState.CREATED.value
    assert run.user_id == persisted_user.id

    mock_schedule_resolution.assert_called_once()
    assert (
        mock_schedule_resolution.call_args.kwargs["rerun_from"]
        == persisted_resolution_w_user.root_id
    )


@mock.patch("sematic.api.endpoints.resolutions.broadcast_pipeline_update")
def test_rerun_resolution_endpoint_auth_different_user(
    mock_broadcast_update: mock.MagicMock,
    persisted_resolution_w_user: Resolution,  # noqa: F811
    persisted_user: User,  # noqa: F811
    other_persisted_user: User,  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811
    test_db,  # noqa: F811
    with_auth,  # noqa: F811
    mock_schedule_resolution: mock.MagicMock,
):
    response = test_client.post(
        f"/api/v1/resolutions/{persisted_resolution_w_user.root_id}/rerun",
        json={"rerun_from": persisted_resolution_w_user.root_id},
        headers=({"X-API-KEY": other_persisted_user.api_key}),
    )

    assert response.status_code == HTTPStatus.OK
    mock_broadcast_update.assert_called()

    payload = response.json
    payload = typing.cast(typing.Dict[str, typing.Any], payload)

    cloned_resolution = get_resolution(payload["content"]["root_id"])

    assert cloned_resolution.status == ResolutionStatus.SCHEDULED.value
    assert cloned_resolution.user_id == other_persisted_user.id

    run = get_run(cloned_resolution.root_id)  # noqa: F811

    assert run.parent_id is None
    assert run.future_state == FutureState.CREATED.value
    assert run.user_id == other_persisted_user.id

    mock_schedule_resolution.assert_called_once()
    assert (
        mock_schedule_resolution.call_args.kwargs["rerun_from"]
        == persisted_resolution_w_user.root_id
    )


@mock.patch("sematic.api.endpoints.resolutions.broadcast_pipeline_update")
def test_rerun_resolution_endpoint_auth_no_user_fails(
    mock_broadcast_update: mock.MagicMock,
    persisted_resolution_w_user: Resolution,  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811
    test_db,  # noqa: F811
    with_auth,  # noqa: F811
    mock_schedule_resolution: mock.MagicMock,
):
    response = test_client.post(
        f"/api/v1/resolutions/{persisted_resolution_w_user.root_id}/rerun",
        json={"rerun_from": persisted_resolution_w_user.root_id},
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    mock_broadcast_update.assert_not_called()


def test_list_external_resources_empty(
    mock_auth, test_client: flask.testing.FlaskClient  # noqa: F811
):
    response = test_client.get("/api/v1/resolutions/abc123/external_resources")

    assert response.status_code == HTTPStatus.OK
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
    assert response.status_code == HTTPStatus.OK

    result_ids = [
        resource["id"]
        for resource in response.json["external_resources"]  # type: ignore
    ]
    assert result_ids == [persisted_external_resource.id]


def _get_expected_env_vars(
    resolution: Resolution, user: User  # noqa: F811
) -> typing.Dict[str, str]:

    expected_env_vars = copy(resolution.settings_env_vars)
    expected_env_vars[str(UserSettingsVar.SEMATIC_API_KEY.value)] = user.api_key
    return expected_env_vars
