# Standard Library
import datetime
import json
import time
import typing
import uuid
from dataclasses import asdict, replace
from unittest import mock
from urllib.parse import urlencode

# Third-party
import flask.testing
import pytest

# Sematic
import sematic.api_client as api_client
from sematic.abstract_future import FutureState
from sematic.api.tests.fixtures import (
    make_auth_test,  # noqa: F401
    mock_auth,  # noqa: F401
    mock_plugin_settings,  # noqa: F401
    mock_requests,  # noqa: F401
    mock_socketio,  # noqa: F401
    test_client,  # noqa: F401; noqa: F401
)
from sematic.config.server_settings import ServerSettings, ServerSettingsVar
from sematic.config.tests.fixtures import empty_settings_file  # noqa: F401
from sematic.config.user_settings import UserSettings, UserSettingsVar
from sematic.db.models.resolution import Resolution, ResolutionKind, ResolutionStatus
from sematic.db.models.run import Run
from sematic.db.models.user import User
from sematic.db.queries import (
    count_jobs_by_run_id,
    get_run,
    save_job,
    save_resolution,
    save_run,
    save_run_external_resource_links,
)
from sematic.db.tests.fixtures import (
    allow_any_run_state_transition,  # noqa: F401
    make_job,  # noqa: F401
    make_resolution,  # noqa: F401
    make_run,  # noqa: F401
    persisted_external_resource,  # noqa: F401
    persisted_resolution,  # noqa: F401
    persisted_run,  # noqa: F401
    persisted_user,  # noqa: F401
    pg_mock,  # noqa: F401
    run,  # noqa: F401
    test_db,  # noqa: F401; noqa: F401
)
from sematic.function import func
from sematic.log_reader import LogLineResult
from sematic.metrics.run_count_metric import RunCountMetric
from sematic.runners.local_runner import LocalRunner
from sematic.scheduling.job_details import PodSummary
from sematic.tests.fixtures import valid_client_version  # noqa: F401
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


@pytest.fixture
def mock_broadcast_graph_update():
    with mock.patch(
        "sematic.api.endpoints.runs.broadcast_graph_update"
    ) as mock_broadcast:
        yield mock_broadcast


@pytest.fixture
def mock_get_run_ids_with_orphaned_jobs():
    with mock.patch(
        "sematic.api.endpoints.runs._GARBAGE_COLLECTION_QUERIES"
    ) as mock_query_dict:
        mock_query = mock.MagicMock()
        mock_query_dict.keys = lambda: ["orphaned_jobs"]
        mock_query_dict.__getitem__ = lambda _, __: mock_query
        yield mock_query


def test_list_runs_empty(
    mock_auth,  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811
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
    assert payload["content"] == [
        dict(user=None, **run_.to_json_encodable()) for run_ in created_runs[:3]
    ]

    next_page_url = payload["next_page_url"]
    next_page_url = next_page_url.split("localhost")[1]

    results = test_client.get(next_page_url)
    payload = results.json
    payload = typing.cast(typing.Dict[str, typing.Any], payload)

    assert payload["next_page_url"] is None
    assert payload["next_cursor"] is None
    assert payload["after_cursor_count"] == 2
    assert payload["content"] == [
        dict(user=None, **run_.to_json_encodable()) for run_ in created_runs[3:]
    ]


def test_list_runs_group_by(
    mock_auth,  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811
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


def test_list_runs_fields(
    mock_auth,  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811
):
    run1 = make_run(name="abc", function_path="abc")
    run2 = make_run(name="def", function_path="abc")

    save_run(run2)
    save_run(run1)

    # test that without "fields" the entire runs are returned
    response = test_client.get("/api/v1/runs")

    assert response.status_code == 200

    payload = response.json
    payload = typing.cast(typing.Dict[str, typing.Any], payload)

    assert len(payload["content"]) == 2

    assert payload["content"][0]["id"] == run1.id
    assert payload["content"][0]["name"] == run1.name
    assert payload["content"][0]["function_path"] == run1.function_path

    assert payload["content"][1]["id"] == run2.id
    assert payload["content"][1]["name"] == run2.name
    assert payload["content"][1]["function_path"] == run2.function_path

    # test that only the specified fields are returned
    query_params = {"fields": json.dumps(["id"])}
    response = test_client.get("/api/v1/runs?{}".format(urlencode(query_params)))

    payload = response.json
    payload = typing.cast(typing.Dict[str, typing.Any], payload)

    assert len(payload["content"]) == 2

    assert payload["content"][0]["id"] == run1.id
    assert len(payload["content"][0]) == 1

    assert payload["content"][1]["id"] == run2.id
    assert len(payload["content"][1]) == 1


def test_list_runs_filters(
    mock_auth,  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811
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
    mock_auth,  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811
):
    run1 = make_run(name="abc", function_path="abc")
    run2 = make_run(name="def", function_path="def")

    for run_ in [run1, run2]:
        save_run(run_)

    filters = json.dumps({"name": {"eq": "ghi"}})

    results = test_client.get(f"/api/v1/runs?filters={filters}")

    payload = results.json
    payload = typing.cast(typing.Dict[str, typing.Any], payload)

    assert len(payload["content"]) == 0


def test_list_runs_and_filters(
    mock_auth,  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811
):
    run1 = make_run(name="abc", function_path="abc")
    run2 = make_run(name="def", function_path="abc")
    run3 = make_run(name="abc", function_path="def")

    for run_ in [run1, run2, run3]:
        save_run(run_)

    filters = {"AND": [{"name": {"eq": "abc"}}, {"function_path": {"eq": "abc"}}]}

    results = test_client.get(f"/api/v1/runs?filters={json.dumps(filters)}")

    payload = results.json
    payload = typing.cast(typing.Dict[str, typing.Any], payload)

    assert len(payload["content"]) == 1
    assert payload["content"][0]["id"] == run1.id


def test_list_runs_or_filters(
    mock_auth,  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811
):
    run1 = make_run(name="abc", function_path="abc")
    run2 = make_run(name="def", function_path="abc")
    run3 = make_run(name="def", function_path="def")

    for run_ in [run1, run2, run3]:
        save_run(run_)

    filters = {"OR": [{"name": {"eq": "abc"}}, {"function_path": {"eq": "def"}}]}

    results = test_client.get(f"/api/v1/runs?filters={json.dumps(filters)}")

    payload = results.json
    payload = typing.cast(typing.Dict[str, typing.Any], payload)

    assert len(payload["content"]) == 2
    assert payload["content"][0]["id"] == run3.id
    assert payload["content"][1]["id"] == run1.id


def test_list_runs_relationship_filters(
    mock_auth,  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811
):
    run1 = make_run(name="abc", function_path="abc")
    run2 = make_run(name="def", function_path="ghi")
    run3 = make_run(name="def", function_path="def")

    for run_ in [run1, run2, run3]:
        save_run(run_)

    run2.root_id = run1.root_id
    save_run(run2)
    resolution1 = make_resolution(root_id=run1.id)
    save_resolution(resolution1)

    resolution2 = make_resolution(root_id=run3.id, kind=ResolutionKind.LOCAL)
    save_resolution(resolution2)

    filters = {
        "OR": [
            {"pipeline_run.kind": {"eq": ResolutionKind.KUBERNETES.value}},
            {"function_path": {"eq": "ghi"}},
        ]
    }

    results = test_client.get(f"/api/v1/runs?filters={json.dumps(filters)}")

    payload = results.json
    payload = typing.cast(typing.Dict[str, typing.Any], payload)

    assert len(payload["content"]) == 2
    function_paths = [result["function_path"] for result in payload["content"]]

    assert run1.function_path in function_paths
    assert run2.function_path in function_paths


def test_list_runs_relationship_filters_errors(
    mock_auth,  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811
):
    # invalid field
    filters = {"non_exist_fld.kind": {"eq": ResolutionKind.KUBERNETES.value}}

    results = test_client.get(f"/api/v1/runs?filters={json.dumps(filters)}")

    assert results.status_code == 400
    assert (
        "is not a field of"
        in typing.cast(typing.Dict[str, typing.Any], results.json)["error"]
    )

    # not relationship field
    filters = {"description.kind": {"eq": ResolutionKind.KUBERNETES.value}}

    results = test_client.get(f"/api/v1/runs?filters={json.dumps(filters)}")

    assert results.status_code == 400
    assert (
        "is not a relationship property"
        in typing.cast(typing.Dict[str, typing.Any], results.json)["error"]
    )

    # field doesn't exist for related model
    filters = {"pipeline_run.non_exist_fld": {"eq": ResolutionKind.KUBERNETES.value}}

    results = test_client.get(f"/api/v1/runs?filters={json.dumps(filters)}")

    assert results.status_code == 400
    payload = typing.cast(typing.Dict[str, typing.Any], results.json)
    assert "is not a field of" in payload["error"] and "Resolution" in payload["error"]

    # unsupported operator
    filters = {"pipeline_run.kind": {"eat": ResolutionKind.KUBERNETES.value}}

    results = test_client.get(f"/api/v1/runs?filters={json.dumps(filters)}")

    assert results.status_code == 400
    assert (
        "only 'eq' is supported"
        in typing.cast(typing.Dict[str, typing.Any], results.json)["error"]
    )


def test_list_runs_limit(
    mock_auth,  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811
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
    mock_auth,  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811
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
    mock_auth,  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811
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
    mock_auth,  # noqa: F811
    persisted_run: Run,  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811
):
    response = test_client.get("/api/v1/runs?limit=bad")

    assert response.status_code == 400

    payload = response.json
    payload = typing.cast(typing.Dict[str, typing.Any], payload)

    assert payload == dict(error="invalid literal for int() with base 10: 'bad'")


def test_list_runs_order_400(
    mock_auth,  # noqa: F811
    persisted_run: Run,  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811
):
    response = test_client.get("/api/v1/runs?order=bad")

    assert response.status_code == 400

    payload = response.json
    payload = typing.cast(typing.Dict[str, typing.Any], payload)

    assert payload == dict(
        error="invalid value for 'order'; expected one of: ['asc', 'desc']; got: 'bad'"
    )


def test_list_runs_cursor_400(
    mock_auth,  # noqa: F811
    persisted_run: Run,  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811
):
    response = test_client.get("/api/v1/runs?cursor=///////")

    assert response.status_code == 400

    payload = response.json
    payload = typing.cast(typing.Dict[str, typing.Any], payload)

    assert payload == dict(error="invalid value for 'cursor'")


def test_list_runs_search_id(
    mock_auth,  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811
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
    mock_auth,  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811
):
    runs = (
        make_run(name="neutrino"),
        make_run(name="neutralino"),
        make_run(name="photon"),
        make_run(function_path="neutralino.to.dark.matter"),
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


def test_list_runs_search_tag_filters(
    mock_auth,  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811
):
    runs = (
        make_run(tags=["food"]),
        make_run(tags=["foo", "bar"]),
        make_run(tags=["foo", "baz"]),
        make_run(tags=["qux", "bar"]),
    )

    for run_ in runs:
        save_run(run_)
    run1, run2, run3, run4 = runs

    def expect(filters, runs):
        filters = dict(filters=json.dumps(filters))
        response = test_client.get(f"/api/v1/runs?{urlencode(filters)}")

        assert response.status_code == 200

        payload = response.json
        payload = typing.cast(typing.Dict[str, typing.Any], payload)
        assert len(payload["content"]) == len(runs)
        assert {run.id for run in runs} == {  # noqa: F811
            r["id"] for r in payload["content"]
        }

    expect({"tags": {"contains": "foo"}}, [run2, run3])
    expect({"tags": {"contains": "food"}}, [run1])
    expect({"tags": {"contains": "oo"}}, [])
    expect(
        {"AND": [{"tags": {"contains": "foo"}}, {"tags": {"contains": "bar"}}]}, [run2]
    )
    expect(
        {"OR": [{"tags": {"contains": "foo"}}, {"tags": {"contains": "bar"}}]},
        [run2, run3, run4],
    )


def test_list_runs_search_tags(
    mock_auth,  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811
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


def test_list_runs_search_orphaned_jobs(
    mock_auth,  # noqa: F811
    mock_get_run_ids_with_orphaned_jobs,  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811
):
    runs = (
        make_run(name="Fox"),
        make_run(name="Falco"),
        make_run(name="Slippy"),
        make_run(name="Peppy"),
    )
    mock_get_run_ids_with_orphaned_jobs.return_value = [r.id for r in runs]

    filters = {"orphaned_jobs": {"eq": True}}
    query_params = {
        "filters": json.dumps(filters),
        "fields": json.dumps(["id"]),
    }
    response = test_client.get("/api/v1/runs?{}".format(urlencode(query_params)))

    assert response.status_code == 200

    payload = response.json
    payload = typing.cast(typing.Dict[str, typing.Any], payload)

    assert len(payload["content"]) == len(runs)
    ids = [result["id"] for result in payload["content"]]
    assert set(ids) == {r.id for r in runs}


def test_get_run_endpoint(
    mock_auth,  # noqa: F811
    persisted_run: Run,  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811
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
        mock_k8s.schedule_run_job.side_effect = lambda *_, **__: make_job(
            name="job1", run_id=persisted_run.id
        )
        persisted_resolution.status = ResolutionStatus.RUNNING
        save_resolution(persisted_resolution)

        with (
            mock.patch(
                "sematic.api.endpoints.runs.broadcast_graph_update"
            ) as mock_broadcast_graph_update,
            mock.patch(
                "sematic.api.endpoints.runs.broadcast_job_update"
            ) as mock_broadcast_job_update,
        ):
            response = test_client.post(f"/api/v1/runs/{persisted_run.id}/schedule")

            mock_broadcast_graph_update.assert_called_once()
            mock_broadcast_job_update.assert_called_once()

        assert response.status_code == 200

        payload = response.json
        run = Run.from_json_encodable(payload["content"])  # type: ignore # noqa: F811
        assert run.future_state == FutureState.SCHEDULED.value
        mock_k8s.schedule_run_job.assert_called_once()
        schedule_job_call_args = mock_k8s.schedule_run_job.call_args[1]
        assert schedule_job_call_args["run_id"] == persisted_run.id
        assert schedule_job_call_args["image"] == persisted_run.container_image_uri
        assert (
            schedule_job_call_args["resource_requirements"]
            == persisted_run.resource_requirements
        )
        run = get_run(persisted_run.id)
        assert count_jobs_by_run_id(run.id) == 1


def test_clean_jobs(
    mock_auth,  # noqa: F811
    persisted_run: Run,  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811
    mock_socketio,  # noqa: F811
):
    with mock.patch("sematic.scheduling.job_scheduler.k8s") as mock_k8s:
        persisted_run.future_state = FutureState.CREATED
        save_run(persisted_run)
        job = make_job(name="job1", run_id=persisted_run.id)
        save_job(job)

        def mock_cancel_job(job):
            details = job.details
            details.canceled = True
            job.details = details
            job.update_status(details.get_status(job.last_updated_epoch_seconds + 1))
            return job

        mock_k8s.cancel_job = mock_cancel_job

        response = test_client.post(f"/api/v1/runs/{persisted_run.id}/clean_jobs")

        # run not terminal yet
        assert response.status_code == 400

        persisted_run.future_state = FutureState.SCHEDULED
        save_run(persisted_run)
        persisted_run.future_state = FutureState.RESOLVED
        save_run(persisted_run)

        response = test_client.post(f"/api/v1/runs/{persisted_run.id}/clean_jobs")
        assert response.status_code == 200
        payload = response.json
        assert payload == {"content": ["DELETED"]}


def test_clean_orphaned_runs(
    mock_auth,  # noqa: F811
    persisted_run: Run,  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811
):
    persisted_run.future_state = FutureState.SCHEDULED
    child_run_1 = make_run(future_state=FutureState.CREATED, root_id=persisted_run.id)
    child_run_2 = make_run(future_state=FutureState.RAN, root_id=persisted_run.id)
    resolution = make_resolution(
        root_id=persisted_run.id, status=ResolutionStatus.RUNNING
    )
    runs = [persisted_run, child_run_1, child_run_2]
    for run in runs:  # noqa: F402
        save_run(run)
    save_resolution(resolution)

    response = test_client.post(f"/api/v1/runs/{persisted_run.id}/clean")

    # resolution not terminal yet
    assert response.status_code == 409

    resolution.status = ResolutionStatus.CANCELED
    save_resolution(resolution)

    for run in runs:
        response = test_client.post(f"/api/v1/runs/{run.id}/clean")
        assert response.status_code == 200

        payload = response.json
        if run.future_state == FutureState.CREATED.value:
            assert payload == {"content": "CANCELED"}
        else:
            assert payload == {"content": "FAILED"}
        assert get_run(run.id).future_state in FutureState.terminal_state_strings()


@mock.patch("sematic.api.endpoints.runs.save_event_metrics")
def test_update_future_states(
    mock_auth,  # noqa: F811
    persisted_run: Run,  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811
    mock_broadcast_graph_update: mock.MagicMock,  # noqa: F811
    mock_socketio: mock.MagicMock,  # noqa: F811
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
        job = make_job(name="job1", run_id=persisted_run.id)
        save_job(job)

        persisted_run.future_state = FutureState.SCHEDULED
        save_run(persisted_run)

        mock_k8s.refresh_job.side_effect = lambda job: job
        with (
            mock.patch("sematic.api.endpoints.runs.broadcast_graph_update"),
            mock.patch("sematic.api.endpoints.runs.broadcast_job_update"),
        ):
            response = test_client.post(
                "/api/v1/runs/future_states", json={"run_ids": [persisted_run.id]}
            )
        assert response.status_code == 200
        payload = response.json
        assert payload == {
            "content": [{"future_state": "SCHEDULED", "run_id": persisted_run.id}]
        }

        # Pretend the job disappeared
        def refresh_job(job):
            job.details = replace(job.details, still_exists=False, has_started=True)
            job.update_status(job.details.get_status(time.time()))
            return job

        mock_k8s.refresh_job.side_effect = refresh_job
        mock_broadcast_graph_update.assert_not_called()
        response = test_client.post(
            "/api/v1/runs/future_states", json={"run_ids": [persisted_run.id]}
        )
        assert response.status_code == 200
        mock_broadcast_graph_update.assert_called_once()
        payload = response.json
        assert payload == {
            "content": [{"future_state": "FAILED", "run_id": persisted_run.id}]
        }


@mock.patch("sematic.api.endpoints.runs.save_event_metrics")
def test_update_run_disappeared(
    mock_auth,  # noqa: F811
    persisted_run: Run,  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811
):
    with mock.patch("sematic.scheduling.job_scheduler.k8s") as mock_k8s:
        job = make_job(name="job1", run_id=persisted_run.id)
        save_job(job)

        persisted_run.future_state = FutureState.SCHEDULED
        save_run(persisted_run)

        # simulate the job disappearing while the run is still SCHEDULED
        # this happens for example when the job is canceled
        details = job.details
        details.has_started = True
        details.still_exists = False
        job.details = details
        job.update_status(details.get_status(time.time()))
        assert not job.latest_status.is_active()
        details.has_infra_failure = True
        job.details = details
        mock_k8s.refresh_job.side_effect = lambda j: job

        with (
            mock.patch(
                "sematic.api.endpoints.runs.broadcast_graph_update"
            ) as mock_broadcast_graph_update,
            mock.patch(
                "sematic.api.endpoints.runs.broadcast_job_update"
            ) as mock_broadcast_job_update,
        ):
            response = test_client.post(
                "/api/v1/runs/future_states", json={"run_ids": [persisted_run.id]}
            )
            mock_broadcast_graph_update.assert_called_once()
            mock_broadcast_job_update.assert_called_once()

        assert response.status_code == 200
        payload = response.json
        assert payload == {
            "content": [{"future_state": "FAILED", "run_id": persisted_run.id}]
        }
        loaded = get_run(persisted_run.id)
        assert loaded.external_exception_metadata == ExceptionMetadata(
            repr="No pods could be found.",
            name="KubernetesError",
            module="sematic.utils.exceptions",
            ancestors=[
                f"{InfrastructureError.__module__}.{InfrastructureError.__name__}",
                f"{Exception.__module__}.{Exception.__name__}",
            ],
        )


@mock.patch("sematic.api.endpoints.runs.save_event_metrics")
def test_update_run_k8_pod_error(
    mock_auth,  # noqa: F811
    persisted_run: Run,  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811
    test_db,  # noqa: F811
    empty_settings_file,  # noqa: F811
):
    with mock.patch("sematic.scheduling.job_scheduler.k8s") as mock_k8s:
        job = make_job(name="job1", run_id=persisted_run.id)
        details = job.details
        details.current_pods = [
            PodSummary(
                pod_name="foo",
                phase="Running",
                has_infra_failure=False,
            ),
        ]
        job.details = details
        save_job(job)

        persisted_run.future_state = FutureState.SCHEDULED
        save_run(persisted_run)

        details = job.details
        details.has_started = True
        details.current_pods = [
            replace(
                details.current_pods[0],
                has_infra_failure=True,
                phase="Failed",
                container_exit_code=42,
                container_condition_message="Pod exited with status code 42",
            ),
        ]
        job.details = details
        job.update_status(details.get_status(time.time()))
        assert not job.latest_status.is_active()
        details.has_infra_failure = True
        job.details = details
        job.update_status(details.get_status(time.time()))
        mock_k8s.refresh_job.side_effect = lambda j: job

        with (
            mock.patch("sematic.api.endpoints.runs.broadcast_graph_update"),
            mock.patch("sematic.api.endpoints.runs.broadcast_job_update"),
        ):
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
            repr="Job failed. Pod exited with status code 42.",
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
        can_continue_forward=True,
        can_continue_backward=True,
        lines=["Line 1", "Line 2"],
        line_ids=[123, 124],
        forward_cursor_token="abc",
        reverse_cursor_token="xyz",
        log_info_message=None,
    )
    mock_load_log_lines.return_value = mock_result
    response = test_client.get(f"/api/v1/runs/{persisted_run.id}/logs")

    payload = response.json
    payload = typing.cast(typing.Dict[str, typing.Any], payload)

    assert payload["content"] == asdict(mock_result)
    kwargs = dict(
        forward_cursor_token="continue...",
        reverse_cursor_token="continue backwards...",
        max_lines=10,
        filter_string="a",
        reverse=False,
    )

    query_string = "&".join(f"{k}={v}" for k, v in kwargs.items())
    test_client.get(f"/api/v1/runs/{persisted_run.id}/logs?{query_string}")

    modified_kwargs = dict(
        forward_cursor_token="continue...",
        reverse_cursor_token="continue backwards...",
        max_lines=10,
        filter_strings=["a"],
        reverse=False,
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
    LocalRunner().run(future)

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
    empty_settings_file,  # noqa: F811
):
    save_run_external_resource_links([persisted_external_resource.id], persisted_run.id)

    response = test_client.get(f"/api/v1/runs/{persisted_run.id}/external_resources")
    assert response.status_code == 200

    payload = response.json
    payload = typing.cast(typing.Dict[str, typing.Any], payload)
    payload = payload["content"]

    assert len(payload) == 1
    assert payload[0]["id"] == persisted_external_resource.id


@mock.patch("sematic.api.endpoints.runs.save_event_metrics")
def test_set_run_user(
    mock_save_event_metrics,
    persisted_user: User,  # noqa: F811
    run: Run,  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811
    mock_requests,  # noqa: F811
    mock_socketio,  # noqa: F811
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
        assert "email" not in payload["content"]["user"]
        assert "api_key" not in payload["content"]["user"]

        response = test_client.get(
            "/api/v1/runs",
            headers={"X-API-KEY": persisted_user.api_key},
        )
        payload = response.json
        payload = typing.cast(typing.Dict[str, typing.Any], payload)

        assert payload["content"][0]["user"]["id"] == persisted_user.id
        assert "email" not in payload["content"][0]["user"]
        assert "api_key" not in payload["content"][0]["user"]


def test_get_jobs(
    mock_socketio,  # noqa: F811
    persisted_user: User,  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811
    persisted_run: Run,  # noqa: F811
    mock_requests,  # noqa: F811
    empty_settings_file,  # noqa: F811
):
    job_1 = make_job(run_id=persisted_run.id, name="job_1")
    job_2 = make_job(run_id=persisted_run.id, name="job_2")
    save_job(job_1)
    save_job(job_2)

    response = test_client.get(f"/api/v1/runs/{persisted_run.id}/jobs")
    serialized_jobs = response.json["content"]  # type: ignore

    for serialized_job in serialized_jobs:
        # don't care about these during comparison
        serialized_job["created_at"] = None
        serialized_job["updated_at"] = None

    assert serialized_jobs == [job_1.to_json_encodable(), job_2.to_json_encodable()]


def test_get_jobs_none_present(
    mock_socketio,  # noqa: F811
    persisted_user: User,  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811
    persisted_run: Run,  # noqa: F811
    mock_requests,  # noqa: F811
    empty_settings_file,  # noqa: F811
):
    response = test_client.get(f"/api/v1/runs/{persisted_run.id}/jobs")
    serialized_jobs = response.json["content"]  # type: ignore
    assert serialized_jobs == []


def test_get_jobs_bad_run_id(
    mock_socketio,  # noqa: F811
    persisted_user: User,  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811
    mock_requests,  # noqa: F811
    empty_settings_file,  # noqa: F811
):
    fake_run_id = 32 * "a"
    response = test_client.get(f"/api/v1/runs/{fake_run_id}/jobs")
    serialized_jobs = response.json["content"]  # type: ignore
    assert serialized_jobs == []


def test_save_graph(
    test_client: flask.testing.FlaskClient,  # noqa: F811
    mock_requests,  # noqa: F811
):
    now = datetime.datetime.utcnow()
    run1 = make_run(created_at=now, updated_at=now)

    test_client.put(
        "/api/v1/graph",
        json={
            "graph": {"runs": [run1.to_json_encodable()], "edges": [], "artifacts": []}
        },
    )

    assert list(RunCountMetric().aggregate(labels={}, group_by=[]).values())[
        0
    ].series == [(1, ())]

    run2 = make_run(created_at=now, updated_at=now)

    test_client.put(
        "/api/v1/graph",
        json={
            "graph": {
                "runs": [run1.to_json_encodable(), run2.to_json_encodable()],
                "edges": [],
                "artifacts": [],
            }
        },
    )

    assert list(RunCountMetric().aggregate(labels={}, group_by=[]).values())[
        0
    ].series == [(2, ())]
