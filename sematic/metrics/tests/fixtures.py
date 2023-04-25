# Standard Library
import datetime
from typing import List

# Third-party
import pytest

# Sematic
from sematic.db.db import DB
from sematic.db.tests.fixtures import test_db  # noqa: F401
from sematic.metrics.metric_point import MetricPoint, MetricType
from sematic.plugins.metrics_storage.sql.sql_metrics_storage import SQLMetricsStorage


@pytest.fixture
def metric_points():
    metric_points = [
        MetricPoint(
            name="foo",
            value=1,
            metric_type=MetricType.GAUGE,
            metric_time=datetime.datetime(2023, 4, 12),
            labels=dict(function_path="foo", root_function_path="bat"),
        ),
        MetricPoint(
            name="foo",
            value=0,
            metric_type=MetricType.GAUGE,
            metric_time=datetime.datetime(2023, 4, 11),
            labels=dict(function_path="bar"),
        ),
        MetricPoint(
            name="bar",
            value=1,
            metric_type=MetricType.COUNT,
            metric_time=datetime.datetime(2023, 4, 12),
            labels=dict(function_path="foo"),
        ),
        MetricPoint(
            name="bar",
            value=1,
            metric_type=MetricType.COUNT,
            metric_time=datetime.datetime(2023, 4, 11),
            labels=dict(function_path="foo"),
        ),
    ]

    return metric_points


@pytest.fixture
def persisted_metric_points(
    metric_points: List[MetricPoint], test_db: DB  # noqa: F811
):
    metrics_storage_plugin = SQLMetricsStorage()

    metrics_storage_plugin.store_metrics(metric_points)

    return metric_points
