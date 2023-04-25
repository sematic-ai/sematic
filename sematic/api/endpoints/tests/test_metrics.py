# Standard Library
import json
from datetime import datetime
from typing import List

# Third-party
import flask.testing
import pytest

# Sematic
from sematic.api.endpoints.metrics import MetricEvent, save_event_metrics
from sematic.api.tests.fixtures import test_client  # noqa: F401
from sematic.db.models.run import Run
from sematic.db.tests.fixtures import (  # noqa: F401
    allow_any_run_state_transition,
    persisted_run,
    run,
    test_db,
)
from sematic.metrics.metric_point import MetricPoint, MetricType
from sematic.metrics.run_count_metric import RunCountMetric
from sematic.metrics.tests.fixtures import (  # noqa: F401
    metric_points,
    persisted_metric_points,
)
from sematic.plugins.abstract_metrics_storage import MetricSeries
from sematic.plugins.metrics_storage.sql.sql_metrics_storage import SQLMetricsStorage


def test_run_created(persisted_run: Run):  # noqa: F811
    save_event_metrics(MetricEvent.run_created, [persisted_run])

    aggregation = RunCountMetric().aggregate(labels={}, group_by=[], rollup=None)

    assert aggregation == {
        SQLMetricsStorage.get_path(): MetricSeries(
            metric_name="sematic.run_count",
            metric_type=MetricType.COUNT.name,
            columns=[],
            series=[(1, ())],
        )
    }


@pytest.mark.parametrize(
    "url, expected_series",
    (
        (
            "foo",
            {
                "metric_name": "foo",
                "series": [[0.5, []]],
                "metric_type": "GAUGE",
                "columns": [],
            },
        ),
        (
            f"foo?labels={json.dumps(dict(function_path='foo'))}",
            {
                "metric_name": "foo",
                "series": [[1, []]],
                "metric_type": "GAUGE",
                "columns": [],
            },
        ),
        (
            "foo?group_by=function_path",
            {
                "metric_name": "foo",
                "series": [[0, ["bar"]], [1, ["foo"]]],
                "metric_type": "GAUGE",
                "columns": ["function_path"],
            },
        ),
        (
            (
                f"foo?from_time={int(datetime(2023, 4, 12).timestamp() - 1)}"
                f"&to_time={int(datetime(2023, 4, 12).timestamp() + 1)}"
            ),
            {
                "metric_name": "foo",
                "series": [[1, []]],
                "metric_type": "GAUGE",
                "columns": [],
            },
        ),
        (
            "foo?rollup=auto",
            {
                "metric_name": "foo",
                "series": [
                    [0, [datetime(2023, 4, 11).timestamp()]],
                    [1, [datetime(2023, 4, 12).timestamp()]],
                ],
                "metric_type": "GAUGE",
                "columns": ["timestamp"],
            },
        ),
        (
            (
                f"foo?rollup={24 * 3600}"
                f"&from_time={int(datetime(2023, 4, 10).timestamp())}"
                f"&to_time={int(datetime(2023, 4, 13).timestamp())}"
            ),
            {
                "metric_name": "foo",
                "series": [
                    [0, [datetime(2023, 4, 11).timestamp()]],
                    [1, [datetime(2023, 4, 12).timestamp()]],
                ],
                "metric_type": "GAUGE",
                "columns": ["timestamp"],
            },
        ),
    ),
)
def test_get_metrics_endpoint(
    url: str,
    expected_series,
    persisted_metric_points: List[MetricPoint],  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811
):
    response = test_client.get(f"/api/v1/metrics/{url}")

    payload = response.json

    assert payload["content"] == expected_series  # type: ignore
