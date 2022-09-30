# Standard Library
import json
import typing
import uuid
from dataclasses import asdict
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
from sematic.calculator import func
from sematic.db.models.resolution import Resolution, ResolutionStatus
from sematic.db.models.run import Run
from sematic.db.queries import get_run, save_resolution, save_run
from sematic.db.tests.fixtures import (  # noqa: F401
    make_run,
    persisted_resolution,
    persisted_run,
    pg_mock,
    run,
    test_db,
)
from sematic.log_reader import LogLineResult
from sematic.scheduling.external_job import JobType
from sematic.scheduling.kubernetes import KubernetesExternalJob
from sematic.tests.fixtures import valid_client_version  # noqa: F401
from sematic.utils.exceptions import ExceptionMetadata

test_list_runs_auth = make_auth_test("/api/v1/runs")
test_get_run_auth = make_auth_test("/api/v1/runs/123")
test_get_run_graph_auth = make_auth_test("/api/v1/runs/123/graph")
test_get_run_logs_graph_auth = make_auth_test("/api/v1/runs/123/logs")
test_put_run_graph_auth = make_auth_test("/api/v1/graph", method="PUT")
test_post_events_auth = make_auth_test("/api/v1/events/namespace/event", method="POST")
test_schedule_run_auth = make_auth_test("/api/v1/runs/123/schedule", method="POST")
test_future_states_auth = make_auth_test("/api/v1/runs/future_states", method="POST")


@pytest.fixture
def mock_load_log_lines():
    with mock.patch("sematic.api.endpoints.runs.load_log_lines") as mock_load:
        yield mock_load


@mock_no_auth
def test_list_runs_empty(test_client: flask.testing.FlaskClient):  # noqa: F811
    results = test_client.get("/api/v1/runs?limit=3")

    assert results.json == dict(
        current_page_url="http://localhost/api/v1/runs?limit=3",
        next_page_url=None,
        limit=3,
        next_cursor=None,
        after_cursor_count=0,
        content=[],
    )


@mock_no_auth
def test_list_runs(test_client: flask.testing.FlaskClient):  # noqa: F811
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


@mock_no_auth
def test_group_by(test_client: flask.testing.FlaskClient):  # noqa: F811
    runs = {key: [make_run(name=key), make_run(name=key)] for key in ("RUN_A", "RUN_B")}

    for name, runs_ in runs.items():
        for run_ in runs_:
            save_run(run_)

    results = test_client.get("/api/v1/runs?group_by=name")

    payload = results.json
    payload = typing.cast(typing.Dict[str, typing.Any], payload)

    assert len(payload["content"]) == 2
    assert {run_["name"] for run_ in payload["content"]} == set(runs)


@mock_no_auth
def test_filters(test_client: flask.testing.FlaskClient):  # noqa: F811
    runs = make_run(), make_run()
    runs[0].parent_id = uuid.uuid4().hex

    for run_ in runs:
        save_run(run_)

    for run_ in runs:
        filters = json.dumps({"parent_id": {"eq": run_.parent_id}})

        results = test_client.get("/api/v1/runs?filters={}".format(filters))

        payload = results.json
        payload = typing.cast(typing.Dict[str, typing.Any], payload)

        assert len(payload["content"]) == 1
        assert payload["content"][0]["id"] == run_.id


@mock_no_auth
def test_and_filters(test_client: flask.testing.FlaskClient):  # noqa: F811
    run1 = make_run(name="abc", calculator_path="abc")
    run2 = make_run(name="def", calculator_path="abc")
    run3 = make_run(name="abc", calculator_path="def")

    for run_ in [run1, run2, run3]:
        save_run(run_)

    filters = {"AND": [{"name": {"eq": "abc"}}, {"calculator_path": {"eq": "abc"}}]}

    results = test_client.get("/api/v1/runs?filters={}".format(json.dumps(filters)))

    payload = results.json
    payload = typing.cast(typing.Dict[str, typing.Any], payload)

    assert len(payload["content"]) == 1
    assert payload["content"][0]["id"] == run1.id


@mock_no_auth
def test_get_run_endpoint(
    persisted_run: Run, test_client: flask.testing.FlaskClient  # noqa: F811
):
    response = test_client.get("/api/v1/runs/{}".format(persisted_run.id))

    payload = response.json
    payload = typing.cast(typing.Dict[str, typing.Any], payload)

    assert payload["content"]["id"] == persisted_run.id


@mock_no_auth
def test_get_run_404(test_client: flask.testing.FlaskClient):  # noqa: F811
    response = test_client.get("/api/v1/runs/unknownid")

    assert response.status_code == 404

    payload = response.json
    payload = typing.cast(typing.Dict[str, typing.Any], payload)

    assert payload == dict(error="No runs with id 'unknownid'")


@mock_no_auth
def test_schedule_run(
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
            most_recent_condition=None,
            has_started=False,
            still_exists=True,
        )
        persisted_resolution.status = ResolutionStatus.RUNNING
        save_resolution(persisted_resolution)
        response = test_client.post(f"/api/v1/runs/{persisted_run.id}/schedule")

        assert response.status_code == 200

        payload = response.json
        run = Run.from_json_encodable(payload["content"])  # type: ignore # noqa: F811
        assert run.future_state == FutureState.SCHEDULED.value
        mock_k8s.schedule_run_job.assert_called_once()
        schedule_job_call_args = mock_k8s.schedule_run_job.call_args[1]
        schedule_job_call_args["run_id"] == persisted_run.id
        schedule_job_call_args["image"] == persisted_resolution.docker_image_uri
        schedule_job_call_args[
            "resource_requirements"
        ] == persisted_run.resource_requirements
        run = get_run(persisted_run.id)
        assert len(run.external_jobs) == 1


@mock_no_auth
def test_update_future_states(
    persisted_run: Run, test_client: flask.testing.FlaskClient  # noqa: F811
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
            most_recent_condition=None,
            has_started=True,
            still_exists=True,
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

        # simulate the job disappearing while the run is still SCHEDULED
        job.still_exists = False
        assert not job.is_active()
        persisted_run.external_jobs = (job,)
        persisted_run.future_state = FutureState.SCHEDULED
        save_run(persisted_run)
        response = test_client.post(
            "/api/v1/runs/future_states", json={"run_ids": [persisted_run.id]}
        )
        assert response.status_code == 200
        payload = response.json
        assert payload == {
            "content": [{"future_state": "FAILED", "run_id": persisted_run.id}]
        }
        loaded = get_run(persisted_run.id)
        assert loaded.exception == ExceptionMetadata(
            repr="The kubernetes job(s) experienced an unknown failure",
            name="InvalidStateTransitionError",
            module="sematic.api.endpoints.runs",
        )


@mock_no_auth
def test_get_run_logs(
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
        log_unavailable_reason=None,
    )
    mock_load_log_lines.return_value = mock_result
    response = test_client.get("/api/v1/runs/{}/logs".format(persisted_run.id))

    payload = response.json
    payload = typing.cast(typing.Dict[str, typing.Any], payload)

    assert payload["content"] == asdict(mock_result)
    kwargs = dict(
        continuation_cursor="continue...",
        max_lines=10,
        filter_string="a",
    )

    response = test_client.get(
        "/api/v1/runs/{}/logs?{}".format(
            persisted_run.id, "&".join(f"{k}={v}" for k, v in kwargs.items())
        ),
    )

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
@mock_no_auth
def test_get_run_graph_endpoint(
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

    response = test_client.get("/api/v1/runs/{}/graph?root={}".format(future.id, root))

    assert response.status_code == 200

    payload = response.json
    payload = typing.cast(typing.Dict[str, typing.Any], payload)

    assert payload["run_id"] == future.id
    assert len(payload["runs"]) == run_count
    assert payload["runs"][0]["id"] == future.id
    assert len(payload["artifacts"]) == artifact_count
    assert len(payload["edges"]) == edge_count
