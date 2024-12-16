# Standard Library
import json
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from unittest import mock

# Third-party
import pytest

# Sematic
from sematic.abstract_future import FutureState
from sematic.api.tests.fixtures import (
    mock_auth,  # noqa: F401
    test_client,  # noqa: F401
)
from sematic.api.tests.fixtures import (  # noqa: F401
    mock_requests as mock_requests_fixture,
)  # noqa: F401
from sematic.api_client import (
    IncompatibleClientError,
    _notify_event,
    block_on_run,
    get_artifact_value_by_id,
    get_runs,
    save_metric_points,
    validate_server_compatibility,
)
from sematic.config.config import get_config
from sematic.db.db import DB
from sematic.db.queries import save_run
from sematic.db.tests.fixtures import (
    make_run,  # noqa: F401
    persisted_artifact,  # noqa: F401
    pg_mock,  # noqa: F401
    test_db,  # noqa: F401
    test_storage,  # noqa: F401; noqa: F401
)
from sematic.metrics.metric_point import MetricPoint
from sematic.metrics.tests.fixtures import metric_points  # noqa: F401
from sematic.plugins.metrics_storage.sql.models.metric_value import (
    MetricValue,
)  # noqa: F401
from sematic.tests.fixtures import valid_client_version  # noqa: F401
from sematic.versions import CURRENT_VERSION, MIN_CLIENT_SERVER_SUPPORTS


@dataclass
class MockRequest:
    method: str = "GET"
    headers: Dict[str, str] = field(
        default_factory=lambda: defaultdict(default_factory=str)  # type: ignore
    )


@dataclass
class MockResponse:
    status_code: int
    json_contents: Dict[str, Any]
    text_contents: Optional[str] = None
    url: str = "http://example.com"
    method: str = "GET"

    def json(self) -> Dict[str, Any]:
        return self.json_contents

    @property
    def text(self) -> str:
        if self.text_contents is None:
            return json.dumps(self.json_contents)
        return self.text_contents

    @property
    def request(self) -> MockRequest:
        return MockRequest(method=self.method)


class ConnectionError(RuntimeError):
    pass


@mock.patch("sematic.api_client.requests")
def test_validate_server_compatibility(mock_requests):
    mock_requests.get.return_value = MockResponse(
        status_code=200,
        json_contents=dict(
            server=CURRENT_VERSION,
            min_client_supported=MIN_CLIENT_SERVER_SUPPORTS,
        ),
    )
    validate_server_compatibility(use_cached=False)
    mock_requests.get.assert_called_once()
    assert mock_requests.get.call_args[0][0] == f"{get_config().api_url}/meta/versions"
    assert mock_requests.get.call_args[1]["headers"]["Content-Type"] == "application/json"
    assert mock_requests.get.call_args[1]["headers"]["X-REQUEST-ID"] is not None


@mock.patch("sematic.api_client.requests")
def test_validate_server_compatibility_bad_json(mock_requests):
    mock_requests.get.return_value = MockResponse(status_code=200, json_contents={})

    def bad_json(*_):
        raise json.JSONDecodeError("", "", 1)

    mock_requests.get.return_value.json = bad_json
    with pytest.raises(IncompatibleClientError):
        validate_server_compatibility(use_cached=False)


@mock.patch("sematic.api_client.requests")
def test_validate_server_compatibility_old_server(mock_requests):
    mock_requests.get.return_value = MockResponse(
        status_code=200,
        json_contents=dict(
            server=(0, 1, 0),
            min_client_supported=(0, 1, 0),
        ),
    )
    with pytest.raises(IncompatibleClientError):
        validate_server_compatibility(use_cached=False)


@mock.patch("sematic.api_client.requests")
def test_validate_server_compatibility_old_client(mock_requests):
    mock_requests.get.return_value = MockResponse(
        status_code=200,
        json_contents=dict(
            server=(2**32, 0, 0),
            # let's HOPE it's safe to assume we will never have billions
            # of major versions...
            min_client_supported=(2**32, 0, 0),
        ),
    )
    with pytest.raises(IncompatibleClientError):
        validate_server_compatibility(use_cached=False)


@mock.patch("sematic.api_client.requests")
def test_validate_server_compatibility_new_server_still_supports(mock_requests):
    mock_requests.get.return_value = MockResponse(
        status_code=200,
        json_contents=dict(
            server=(2**32, 0, 0),
            min_client_supported=MIN_CLIENT_SERVER_SUPPORTS,
        ),
    )
    validate_server_compatibility(use_cached=False)
    validate_server_compatibility(use_cached=True)

    mock_requests.get.assert_called_once()


def test_get_artifact_value_by_id(
    mock_requests_fixture,  # noqa: F811
    persisted_artifact,  # noqa: F811
):
    value = get_artifact_value_by_id(persisted_artifact.id)

    assert isinstance(value, int)
    assert value == 42


@mock.patch("sematic.api_client.requests")
def test_notify_resilient(mock_requests):
    mock_requests.post.side_effect = RuntimeError("Intentional fail!")

    # Shouldn't raise
    _notify_event("foo", "bar", {})

    mock_requests.post.assert_called()


@mock.patch("sematic.api_client._notify_event")
def test_save_metrics_points(
    mock_notify_event: mock.MagicMock,
    metric_points: List[MetricPoint],  # noqa: F811
    test_db: DB,  # noqa: F811
    mock_requests_fixture,  # noqa: F811
):
    save_metric_points(metric_points)

    payload = dict(
        metric_points=[
            {
                "name": metric_point.name,
                "value": metric_point.value,
                "metric_type": metric_point.metric_type.value,
                "metric_time": metric_point.metric_time.timestamp(),
                "labels": metric_point.labels,
            }
            for metric_point in metric_points
        ]
    )

    mock_notify_event.assert_called_once_with("metrics", "update", payload)

    with test_db.get_session() as session:
        assert session.query(MetricValue).count() == len(metric_points)


def test_list_runs(test_db, mock_requests_fixture):  # noqa: F811
    created_runs = [
        save_run(make_run(name="foo" if i % 2 == 0 else "bar")) for i in range(5)
    ]

    created_runs = sorted(created_runs, key=lambda run_: run_.created_at, reverse=True)

    results = get_runs(limit=1, order="desc", id=created_runs[3].id)
    assert len(results) == 1
    assert results[0].id == created_runs[3].id

    results = get_runs(limit=1, order="desc", name="foo")
    assert len(results) == 1
    assert results[0].name == "foo"

    results = get_runs(limit=5, order="desc", name="foo")
    assert len(results) == 3
    assert all(r.name == "foo" for r in results)

    results = get_runs()
    assert set(r.id for r in results) == set(r.id for r in created_runs)

    ids_desc = [r.id for r in get_runs(limit=5, order="desc")]
    ids_asc = [r.id for r in get_runs(limit=5, order="asc")]
    assert ids_desc == list(reversed(ids_asc))


@mock.patch("sematic.api_client.get_run")
def test_block_on_run(mock_get_run: mock.MagicMock):  # noqa: F811
    created_run = make_run(name="foo", future_state=FutureState.SCHEDULED)

    def fake_get_run(run_id):
        if mock_get_run.call_count >= 3:
            created_run.future_state = FutureState.RESOLVED
        return created_run

    mock_get_run.side_effect = fake_get_run

    block_on_run(created_run.id, polling_interval_seconds=0.01, max_wait_seconds=5)

    # unsuccessful run
    mock_get_run.reset_mock()
    created_run.future_state = FutureState.SCHEDULED

    def get_unsuccessful_run(run_id):
        if mock_get_run.call_count >= 3:
            created_run.future_state = FutureState.FAILED
        return created_run

    mock_get_run.side_effect = get_unsuccessful_run

    with pytest.raises(RuntimeError):
        block_on_run(created_run.id, polling_interval_seconds=0.01, max_wait_seconds=5)

    # Long run
    mock_get_run.reset_mock()
    created_run.future_state = FutureState.SCHEDULED

    def get_long_run(run_id):
        return created_run

    mock_get_run.side_effect = get_long_run

    with pytest.raises(TimeoutError):
        block_on_run(created_run.id, polling_interval_seconds=0.01, max_wait_seconds=0.5)
