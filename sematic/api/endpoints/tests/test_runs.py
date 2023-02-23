# Standard Library
import datetime
import json
import typing
import uuid
from dataclasses import asdict
from unittest import mock

# Third-party
import flask.testing
import pytest

# Sematic
import sematic.api_client as api_client
from sematic.abstract_future import FutureState
from sematic.api.tests.fixtures import (  # noqa: F401
    make_auth_test,
    mock_auth,
    mock_plugin_settings,
    mock_requests,
    mock_socketio,
    test_client,
)
from sematic.calculator import func
from sematic.config.server_settings import ServerSettings, ServerSettingsVar
from sematic.config.tests.fixtures import empty_settings_file  # noqa: F401
from sematic.config.user_settings import UserSettings, UserSettingsVar
from sematic.db.models.resolution import Resolution, ResolutionStatus
from sematic.db.models.run import Run
from sematic.db.models.user import User
from sematic.db.queries import (
    get_run,
    save_resolution,
    save_run,
    save_run_external_resource_links,
)
from sematic.db.tests.fixtures import (  # noqa: F401
    make_run,
    persisted_external_resource,
    persisted_resolution,
    persisted_run,
    persisted_user,
    pg_mock,
    run,
    test_db,
)
from sematic.log_reader import LogLineResult
from sematic.scheduling.external_job import JobType
from sematic.scheduling.kubernetes import KubernetesExternalJob
from sematic.tests.fixtures import MockStorage, valid_client_version  # noqa: F401
from sematic.utils.exceptions import ExceptionMetadata, InfrastructureError

test_list_runs_auth = make_auth_test("/api/v1/runs")
test_get_run_auth = make_auth_test("/api/v1/runs/123")
test_get_run_graph_auth = make_auth_test("/api/v1/runs/123/graph")
test_get_run_logs_graph_auth = make_auth_test("/api/v1/runs/123/logs")
test_put_run_graph_auth = make_auth_test("/api/v1/graph", method="PUT")
test_post_events_auth = make_auth_test("/api/v1/events/namespace/event", method="POST")
test_schedule_run_auth = make_auth_test("/api/v1/runs/123/schedule", method="POST")
test_future_states_auth = make_auth_test("/api/v1/runs/future_states", method="POST")
test_get_run_external_resource_auth = make_auth_test(
    "/api/v1/runs/abc123/external_resources", method="GET"
)


@pytest.fixture
def mock_load_log_lines():
    with mock.patch("sematic.api.endpoints.runs.load_log_lines") as mock_load:
        yield mock_load


def test_list_runs_empty(
    mock_auth, test_client: flask.testing.FlaskClient  # noqa: F811
):
    results = test_client.get("/api/v1/runs?limit=3")

    assert results.json == dict(
        current_page_url="http://localhost/api/v1/runs?limit=3",
        next_page_url=None,
        limit=3,
        next_cursor=None,
        after_cursor_count=0,
        content=[],
    )


def test_list_runs(mock_auth, test_client: flask.testing.FlaskClient):  # noqa: F811
    created_runs = [save_run(make_run()) for _ in range(5)]

    # Sort by latest
    created_runs = sorted(created_runs, key=lambda run_: run_.created_at, reverse=True)

    results = test_client.get("/api/v1/runs?limit=3")

    payload = results.json
    payload = typing.cast(typing.Dict[str, typing.Any], payload)

    assert len(payload["next_page_url"]) > 0
    assert len(payload["next_cursor"]) > 0
    assert payload["after_cursor_count"] == len(created_runs)
    assert payload["content"] == [run_.to_json_encodable() for run_ in created_runs[:3]]

    next_page_url = payload["next_page_url"]
    next_page_url = next_page_url.split("localhost")[1]

    results = test_client.get(next_page_url)
    payload = results.json
    payload = typing.cast(typing.Dict[str, typing.Any], payload)

    assert payload["next_page_url"] is None
    assert payload["next_cursor"] is None
    assert payload["after_cursor_count"] == 2
    assert payload["content"] == [run_.to_json_encodable() for run_ in created_runs[3:]]


def test_list_runs_group_by(
    mock_auth, test_client: flask.testing.FlaskClient  # noqa: F811
):
    runs = {key: [make_run(name=key), make_run(name=key)] for key in ("RUN_A", "RUN_B")}

    for name, runs_ in runs.items():
        for run_ in runs_:
            save_run(run_)

    results = test_client.get("/api/v1/runs?group_by=name")

    payload = results.json
    payload = typing.cast(typing.Dict[str, typing.Any], payload)

    assert len(payload["content"]) == 2
    assert {run_["name"] for run_ in payload["content"]} == set(runs)


def test_list_runs_filters(
    mock_auth, test_client: flask.testing.FlaskClient  # noqa: F811
):
    runs = make_run(), make_run()
    runs[0].parent_id = uuid.uuid4().hex

    for run_ in runs:
        save_run(run_)

    for run_ in runs:
        filters = json.dumps({"parent_id": {"eq": run_.parent_id}})

        results = test_client.get(f"/api/v1/runs?filters={filters}")

        payload = results.json
        payload = typing.cast(typing.Dict[str, typing.Any], payload)

        assert len(payload["content"]) == 1
        assert payload["content"][0]["id"] == run_.id


def test_list_runs_filters_empty(
    mock_auth, test_client: flask.testing.FlaskClient  # noqa: F811
):
    run1 = make_run(name="abc", calculator_path="abc")
    run2 = make_run(name="def", calculator_path="def")

    for run_ in [run1, run2]:
        save_run(run_)

    filters = json.dumps({"name": {"eq": "ghi"}})

    results = test_client.get(f"/api/v1/runs?filters={filters}")

    payload = results.json
    payload = typing.cast(typing.Dict[str, typing.Any], payload)

    assert len(payload["content"]) == 0


def test_list_runs_and_filters(
    mock_auth, test_client: flask.testing.FlaskClient  # noqa: F811
):
    run1 = make_run(name="abc", calculator_path="abc")
    run2 = make_run(name="def", calculator_path="abc")
    run3 = make_run(name="abc", calculator_path="def")

    for run_ in [run1, run2, run3]:
        save_run(run_)

    filters = {"AND": [{"name": {"eq": "abc"}}, {"calculator_path": {"eq": "abc"}}]}

    results = test_client.get(f"/api/v1/runs?filters={json.dumps(filters)}")

    payload = results.json
    payload = typing.cast(typing.Dict[str, typing.Any], payload)

    assert len(payload["content"]) == 1
    assert payload["content"][0]["id"] == run1.id


def test_list_runs_or_filters(
    mock_auth, test_client: flask.testing.FlaskClient  # noqa: F811
):
    run1 = make_run(name="abc", calculator_path="abc")
    run2 = make_run(name="def", calculator_path="abc")
    run3 = make_run(name="def", calculator_path="def")

    for run_ in [run1, run2, run3]:
        save_run(run_)

    filters = {"OR": [{"name": {"eq": "abc"}}, {"calculator_path": {"eq": "def"}}]}

    results = test_client.get(f"/api/v1/runs?filters={json.dumps(filters)}")

    payload = results.json
    payload = typing.cast(typing.Dict[str, typing.Any], payload)

    assert len(payload["content"]) == 2
    assert payload["content"][0]["id"] == run3.id
    assert payload["content"][1]["id"] == run1.id


def test_list_runs_limit(
    mock_auth, test_client: flask.testing.FlaskClient  # noqa: F811
):
    run1, run2, run3 = make_run(), make_run(), make_run()

    for run_ in [run1, run2, run3]:
        save_run(run_)

    results = test_client.get("/api/v1/runs?limit=2")

    payload = results.json
    payload = typing.cast(typing.Dict[str, typing.Any], payload)

    assert len(payload["content"]) == 2
    assert payload["content"][0]["id"] == run3.id
    assert payload["content"][1]["id"] == run2.id


def test_list_runs_order_asc(
    mock_auth, test_client: flask.testing.FlaskClient  # noqa: F811
):
    now = datetime.datetime.utcnow()
    run1 = make_run(created_at=now + datetime.timedelta(seconds=1))
    run2 = make_run(created_at=now + datetime.timedelta(seconds=2))
    run3 = make_run(created_at=now + datetime.timedelta(seconds=3))

    for run_ in [run1, run2, run3]:
        save_run(run_)

    results = test_client.get("/api/v1/runs?order=asc")

    payload = results.json
    payload = typing.cast(typing.Dict[str, typing.Any], payload)

    assert len(payload["content"]) == 3
    assert payload["content"][0]["id"] == run1.id
    assert payload["content"][1]["id"] == run2.id
    assert payload["content"][2]["id"] == run3.id


def test_list_runs_order_desc(
    mock_auth, test_client: flask.testing.FlaskClient  # noqa: F811
):
    now = datetime.datetime.utcnow()
    run1 = make_run(created_at=now + datetime.timedelta(seconds=1))
    run2 = make_run(created_at=now + datetime.timedelta(seconds=2))
    run3 = make_run(created_at=now + datetime.timedelta(seconds=3))

    for run_ in [run1, run2, run3]:
        save_run(run_)

    results = test_client.get("/api/v1/runs?order=desc")

    payload = results.json
    payload = typing.cast(typing.Dict[str, typing.Any], payload)

    assert len(payload["content"]) == 3
    assert payload["content"][0]["id"] == run3.id
    assert payload["content"][1]["id"] == run2.id
    assert payload["content"][2]["id"] == run1.id


def test_list_runs_limit_400(
    mock_auth, persisted_run: Run, test_client: flask.testing.FlaskClient  # noqa: F811
):
    response = test_client.get("/api/v1/runs?limit=bad")

    assert response.status_code == 400

    payload = response.json
    payload = typing.cast(typing.Dict[str, typing.Any], payload)

    assert payload == dict(error="invalid literal for int() with base 10: 'bad'")


def test_list_runs_order_400(
    mock_auth, persisted_run: Run, test_client: flask.testing.FlaskClient  # noqa: F811
):
    response = test_client.get("/api/v1/runs?order=bad")

    assert response.status_code == 400

    payload = response.json
    payload = typing.cast(typing.Dict[str, typing.Any], payload)

    assert payload == dict(
        error="invalid value for 'order'; expected one of: ['asc', 'desc']; got: 'bad'"
    )


def test_list_runs_cursor_400(
    mock_auth, persisted_run: Run, test_client: flask.testing.FlaskClient  # noqa: F811
):
    response = test_client.get("/api/v1/runs?cursor=///////")

    assert response.status_code == 400

    payload = response.json
    payload = typing.cast(typing.Dict[str, typing.Any], payload)

    assert payload == dict(error="invalid value for 'cursor'")


def test_list_runs_search_id(
    mock_auth, test_client: flask.testing.FlaskClient  # noqa: F811
):
    runs = make_run(), make_run(), make_run()

    for run_ in runs:
        save_run(run_)

    run1 = runs[0]

    response = test_client.get(f"/api/v1/runs?search={run1.id}")

    assert response.status_code == 200

    payload = response.json
    payload = typing.cast(typing.Dict[str, typing.Any], payload)

    assert len(payload["content"]) == 1
    assert payload["content"][0]["id"] == run1.id


def test_list_runs_search_fields(
    mock_auth, test_client: flask.testing.FlaskClient  # noqa: F811
):
    runs = (
        make_run(name="neutrino"),
        make_run(name="neutralino"),
        make_run(name="photon"),
        make_run(calculator_path="neutralino.to.dark.matter"),
        make_run(description="the neutralino is a hypothetical particle"),
    )

    for run_ in runs:
        save_run(run_)
    run1, run2, run3, run4, run5 = runs

    response = test_client.get("/api/v1/runs?search=neutr")

    assert response.status_code == 200

    payload = response.json
    payload = typing.cast(typing.Dict[str, typing.Any], payload)

    assert len(payload["content"]) == 4
    ids = [result["id"] for result in payload["content"]]
    assert run1.id in ids
    assert run2.id in ids
    assert run3.id not in ids
    assert run4.id in ids
    assert run5.id in ids


def test_list_runs_search_tags(
    mock_auth, test_client: flask.testing.FlaskClient  # noqa: F811
):
    runs = (
        make_run(tags=["Donald", "Fauntleroy"]),
        make_run(tags=["Pineapple", "apple", "pie"]),
        make_run(tags=["MacDonald"]),
    )

    for run_ in runs:
        save_run(run_)
    run1, run2, run3 = runs

    response = test_client.get("/api/v1/runs?search=donald")

    assert response.status_code == 200

    payload = response.json
    payload = typing.cast(typing.Dict[str, typing.Any], payload)

    assert len(payload["content"]) == 2
    ids = [result["id"] for result in payload["content"]]
    assert run1.id in ids
    assert run2.id not in ids
    assert run3.id in ids


def test_get_run_endpoint(
    mock_auth, persisted_run: Run, test_client: flask.testing.FlaskClient  # noqa: F811
):
    response = test_client.get(f"/api/v1/runs/{persisted_run.id}")

    payload = response.json
    payload = typing.cast(typing.Dict[str, typing.Any], payload)

    assert payload["content"]["id"] == persisted_run.id


def test_get_run_404(mock_auth, test_client: flask.testing.FlaskClient):  # noqa: F811
    response = test_client.get("/api/v1/runs/unknownid")

    assert response.status_code == 404

    payload = response.json
    payload = typing.cast(typing.Dict[str, typing.Any], payload)

    assert payload == dict(error="No runs with id 'unknownid'")


def test_schedule_run(
    mock_auth,  # noqa: F811
    persisted_run: Run,  # noqa: F811
    persisted_resolution: Resolution,  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811
):
    with mock.patch("sematic.scheduling.job_scheduler.k8s") as mock_k8s:
        mock_k8s.refresh_job.side_effect = lambda job: job
        mock_k8s.schedule_run_job.side_effect = lambda *_, **__: KubernetesExternalJob(
            kind="k8s",
            try_number=0,
            external_job_id=KubernetesExternalJob.make_external_job_id(
                persisted_run.id, namespace="foo", job_type=JobType.worker
            ),
            pending_or_running_pod_count=1,
            succeeded_pod_count=0,
            has_started=False,
            still_exists=True,
            start_time=None,
            most_recent_condition=None,
            most_recent_pod_phase_message=None,
            most_recent_pod_condition_message=None,
            most_recent_container_condition_message=None,
            has_infra_failure=False,
        )
        persisted_resolution.status = ResolutionStatus.RUNNING
        save_resolution(persisted_resolution)

        with mock.patch(
            "sematic.api.endpoints.runs.broadcast_graph_update"
        ) as mock_broadcast_graph_update:
            response = test_client.post(f"/api/v1/runs/{persisted_run.id}/schedule")

            mock_broadcast_graph_update.assert_called_once()

        assert response.status_code == 200

        payload = response.json
        run = Run.from_json_encodable(payload["content"])  # type: ignore # noqa: F811
        assert run.future_state == FutureState.SCHEDULED.value
        mock_k8s.schedule_run_job.assert_called_once()
        schedule_job_call_args = mock_k8s.schedule_run_job.call_args[1]
        schedule_job_call_args["run_id"] == persisted_run.id
        schedule_job_call_args["image"] == persisted_run.container_image_uri
        schedule_job_call_args[
            "resource_requirements"
        ] == persisted_run.resource_requirements
        run = get_run(persisted_run.id)
        assert len(run.external_jobs) == 1


def test_update_future_states(
    mock_auth, persisted_run: Run, test_client: flask.testing.FlaskClient  # noqa: F811
):
    with mock.patch("sematic.scheduling.job_scheduler.k8s") as mock_k8s:
        persisted_run.future_state = FutureState.CREATED
        save_run(persisted_run)
        response = test_client.post(
            "/api/v1/runs/future_states", json={"run_ids": [persisted_run.id]}
        )

        assert response.status_code == 200
        payload = response.json
        assert payload == {
            "content": [{"future_state": "CREATED", "run_id": persisted_run.id}]
        }
        job = KubernetesExternalJob(
            kind="k8s",
            try_number=0,
            external_job_id=KubernetesExternalJob.make_external_job_id(
                persisted_run.id, namespace="foo", job_type=JobType.worker
            ),
            pending_or_running_pod_count=1,
            succeeded_pod_count=0,
            has_started=True,
            still_exists=True,
            start_time=1.01,
            most_recent_condition=None,
            most_recent_pod_phase_message=None,
            most_recent_pod_condition_message=None,
            most_recent_container_condition_message=None,
            has_infra_failure=False,
        )

        persisted_run.external_jobs = (job,)
        persisted_run.future_state = FutureState.SCHEDULED
        save_run(persisted_run)

        mock_k8s.refresh_job.side_effect = lambda job: job
        response = test_client.post(
            "/api/v1/runs/future_states", json={"run_ids": [persisted_run.id]}
        )
        assert response.status_code == 200
        payload = response.json
        assert payload == {
            "content": [{"future_state": "SCHEDULED", "run_id": persisted_run.id}]
        }


def test_update_run_disappeared(
    mock_auth, persisted_run: Run, test_client: flask.testing.FlaskClient  # noqa: F811
):
    with mock.patch("sematic.scheduling.job_scheduler.k8s") as mock_k8s:

        job = KubernetesExternalJob(
            kind="k8s",
            try_number=0,
            external_job_id=KubernetesExternalJob.make_external_job_id(
                persisted_run.id, namespace="foo", job_type=JobType.worker
            ),
            pending_or_running_pod_count=1,
            succeeded_pod_count=0,
            has_started=True,
            still_exists=True,
            start_time=1.01,
            most_recent_condition=None,
            most_recent_pod_phase_message=None,
            most_recent_pod_condition_message=None,
            most_recent_container_condition_message=None,
            has_infra_failure=False,
        )

        persisted_run.external_jobs = (job,)
        persisted_run.future_state = FutureState.SCHEDULED
        save_run(persisted_run)

        # simulate the job disappearing while the run is still SCHEDULED
        # this happens for example when the job is canceled
        job.still_exists = False
        assert not job.is_active()
        job.has_infra_failure = True
        mock_k8s.refresh_job.side_effect = lambda j: job

        with mock.patch(
            "sematic.api.endpoints.runs.broadcast_graph_update"
        ) as mock_broadcast_graph_update:
            response = test_client.post(
                "/api/v1/runs/future_states", json={"run_ids": [persisted_run.id]}
            )
            mock_broadcast_graph_update.assert_called_once()

        assert response.status_code == 200
        payload = response.json
        assert payload == {
            "content": [{"future_state": "FAILED", "run_id": persisted_run.id}]
        }
        loaded = get_run(persisted_run.id)
        assert loaded.external_exception_metadata == ExceptionMetadata(
            repr="The Kubernetes job state is unknown",
            name="KubernetesError",
            module="sematic.utils.exceptions",
            ancestors=[
                f"{InfrastructureError.__module__}.{InfrastructureError.__name__}",
                f"{Exception.__module__}.{Exception.__name__}",
            ],
        )


def test_update_run_k8_pod_error(
    mock_auth, persisted_run: Run, test_client: flask.testing.FlaskClient  # noqa: F811
):
    with mock.patch("sematic.scheduling.job_scheduler.k8s") as mock_k8s:

        job = KubernetesExternalJob(
            kind="k8s",
            try_number=0,
            external_job_id=KubernetesExternalJob.make_external_job_id(
                persisted_run.id, namespace="foo", job_type=JobType.worker
            ),
            pending_or_running_pod_count=1,
            succeeded_pod_count=0,
            has_started=True,
            still_exists=True,
            start_time=1.01,
            most_recent_condition=None,
            most_recent_pod_phase_message=None,
            most_recent_pod_condition_message=None,
            most_recent_container_condition_message=None,
            has_infra_failure=False,
        )

        persisted_run.external_jobs = (job,)
        persisted_run.future_state = FutureState.SCHEDULED
        save_run(persisted_run)

        job.still_exists = False
        assert not job.is_active()
        job.has_infra_failure = True
        job.most_recent_pod_phase_message = "Failed"
        job.most_recent_pod_condition_message = "test pod condition"
        job.most_recent_container_condition_message = "test container condition"
        mock_k8s.refresh_job.side_effect = lambda j: job

        response = test_client.post(
            "/api/v1/runs/future_states", json={"run_ids": [persisted_run.id]}
        )
        assert response.status_code == 200
        payload = response.json
        assert payload == {
            "content": [{"future_state": "FAILED", "run_id": persisted_run.id}]
        }
        loaded = get_run(persisted_run.id)
        assert loaded.external_exception_metadata == ExceptionMetadata(
            repr="Failed\ntest pod condition\ntest container condition",
            name="KubernetesError",
            module="sematic.utils.exceptions",
            ancestors=[
                f"{InfrastructureError.__module__}.{InfrastructureError.__name__}",
                f"{Exception.__module__}.{Exception.__name__}",
            ],
        )


def test_get_run_logs(
    mock_auth,  # noqa: F811
    mock_load_log_lines,
    persisted_resolution: Resolution,  # noqa: F811
    persisted_run: Run,  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811
):
    mock_result = LogLineResult(
        more_before=False,
        more_after=True,
        lines=["Line 1", "Line 2"],
        continuation_cursor="abc",
        log_info_message=None,
    )
    mock_load_log_lines.return_value = mock_result
    response = test_client.get(f"/api/v1/runs/{persisted_run.id}/logs")

    payload = response.json
    payload = typing.cast(typing.Dict[str, typing.Any], payload)

    assert payload["content"] == asdict(mock_result)
    kwargs = dict(
        continuation_cursor="continue...",
        max_lines=10,
        filter_string="a",
    )

    query_string = "&".join(f"{k}={v}" for k, v in kwargs.items())
    test_client.get(f"/api/v1/runs/{persisted_run.id}/logs?{query_string}")

    modified_kwargs = dict(
        continuation_cursor="continue...",
        max_lines=10,
        filter_strings=["a"],
    )
    mock_load_log_lines.assert_called_with(
        run_id=persisted_run.id,
        **modified_kwargs,
    )


@func
def add(a: float, b: float) -> float:
    return a + b


@func
def pipeline(a: float, b: float) -> float:
    return add(add(a, b), b)


@pytest.mark.parametrize(
    "root, run_count, artifact_count, edge_count", ((0, 1, 3, 3), (1, 3, 4, 8))
)
def test_get_run_graph_endpoint(
    mock_socketio,  # noqa: F811
    mock_auth,  # noqa: F811
    root: int,
    run_count: int,
    artifact_count: int,
    edge_count: int,
    test_client: flask.testing.FlaskClient,  # noqa: F811
    mock_requests,  # noqa: F811
    valid_client_version,  # noqa: F811
):
    future = pipeline(1, 2)
    future.resolve()

    response = test_client.get(f"/api/v1/runs/{future.id}/graph?root={root}")

    assert response.status_code == 200

    payload = response.json
    payload = typing.cast(typing.Dict[str, typing.Any], payload)

    assert payload["run_id"] == future.id
    assert len(payload["runs"]) == run_count
    assert payload["runs"][0]["id"] == future.id
    assert len(payload["artifacts"]) == artifact_count
    assert len(payload["edges"]) == edge_count


def test_get_run_external_resources(
    persisted_run,  # noqa: F811
    persisted_external_resource,  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811
):
    save_run_external_resource_links([persisted_external_resource.id], persisted_run.id)

    response = test_client.get(f"/api/v1/runs/{persisted_run.id}/external_resources")
    assert response.status_code == 200

    payload = response.json
    payload = typing.cast(typing.Dict[str, typing.Any], payload)
    payload = payload["content"]

    assert len(payload) == 1
    assert payload[0]["id"] == persisted_external_resource.id


def test_set_run_user(
    persisted_user: User,  # noqa: F811
    run: Run,  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811
    mock_requests,  # noqa: F811
    empty_settings_file,  # noqa: F811
):
    with mock_plugin_settings(
        ServerSettings, {ServerSettingsVar.SEMATIC_AUTHENTICATE: "1"}
    ):
        with mock_plugin_settings(
            UserSettings, {UserSettingsVar.SEMATIC_API_KEY: persisted_user.api_key}
        ):
            api_client.save_graph(run.id, [run], [], [])

            saved_run = api_client.get_run(run.id)

            assert saved_run.user_id is not None
            assert saved_run.user_id == persisted_user.id

        response = test_client.get(
            f"/api/v1/runs/{saved_run.id}",
            headers={"X-API-KEY": persisted_user.api_key},
        )
        payload = response.json
        payload = typing.cast(typing.Dict[str, typing.Any], payload)

        assert payload["content"]["user"]["id"] == persisted_user.id
        assert payload["content"]["user"]["email"] == "REDACTED"
        assert payload["content"]["user"]["api_key"] == "REDACTED"

        response = test_client.get(
            f"/api/v1/runs",
            headers={"X-API-KEY": persisted_user.api_key},
        )
        payload = response.json
        payload = typing.cast(typing.Dict[str, typing.Any], payload)

        assert payload["content"][0]["user"]["id"] == persisted_user.id
        assert payload["content"][0]["user"]["email"] == "REDACTED"
        assert payload["content"][0]["user"]["api_key"] == "REDACTED"
