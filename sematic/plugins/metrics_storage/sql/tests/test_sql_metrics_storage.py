# Standard Library
import datetime
from typing import List, Literal, Union

# Third-party
import pytest

# Sematic
from sematic.db.db import DB
from sematic.db.tests.fixtures import test_db  # noqa: F401
from sematic.metrics.metric_point import MetricPoint, MetricType
from sematic.plugins.abstract_metrics_storage import (
    GroupBy,
    MetricSeries,
    MetricsFilter,
)
from sematic.plugins.metrics_storage.sql.models.metric_label import MetricLabel
from sematic.plugins.metrics_storage.sql.models.metric_value import MetricValue
from sematic.plugins.metrics_storage.sql.sql_metrics_storage import SQLMetricsStorage


@pytest.fixture
def metric_points():
    metric_points = [
        MetricPoint(
            name="foo",
            value=1,
            metric_type=MetricType.GAUGE,
            metric_time=datetime.datetime(2023, 4, 12),
            labels=dict(function_path="foo"),
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


def test_store_metrics(test_db: DB, metric_points: List[MetricPoint]):  # noqa: F811
    metrics_storage_plugin = SQLMetricsStorage()

    metrics_storage_plugin.store_metrics(metric_points)

    with test_db.get_session() as session:
        metric_label_count = session.query(MetricLabel).count()
        metric_value_count = session.query(MetricValue).count()

    assert metric_label_count == 3
    assert metric_value_count == 4


@pytest.mark.parametrize(
    "metrics_filter, group_by, rollup, expected_series",
    (
        (
            MetricsFilter(
                name="foo",
                from_time=datetime.datetime.fromtimestamp(0),
                to_time=datetime.datetime.utcnow(),
                labels={},
            ),
            [],
            None,
            MetricSeries(
                metric_name="foo",
                metric_type=MetricType.GAUGE.name,
                series=[(0.5, ())],
                columns=[],
            ),
        ),
        (
            MetricsFilter(
                name="foo",
                from_time=datetime.datetime(2023, 4, 10),
                to_time=datetime.datetime(2023, 4, 13),
                labels={},
            ),
            [],
            24 * 3600,
            MetricSeries(
                metric_name="foo",
                metric_type=MetricType.GAUGE.name,
                series=[(0, (1681171200,)), (1, (1681257600,))],
                columns=["timestamp"],
            ),
        ),
        (
            MetricsFilter(
                name="foo",
                from_time=datetime.datetime.fromtimestamp(0),
                to_time=datetime.datetime.utcnow(),
                labels={"function_path": "foo"},
            ),
            [GroupBy.function_path],
            None,
            MetricSeries(
                metric_name="foo",
                metric_type=MetricType.GAUGE.name,
                series=[(1, ("foo",))],
                columns=["function_path"],
            ),
        ),
        (
            MetricsFilter(
                name="bar",
                from_time=datetime.datetime.fromtimestamp(0),
                to_time=datetime.datetime.utcnow(),
                labels={},
            ),
            [],
            None,
            MetricSeries(
                metric_name="bar",
                metric_type=MetricType.COUNT.name,
                series=[(2, ())],
                columns=[],
            ),
        ),
        (
            MetricsFilter(
                name="bar",
                from_time=datetime.datetime(2023, 4, 10),
                to_time=datetime.datetime(2023, 4, 13),
                labels={},
            ),
            [GroupBy.function_path],
            24 * 3600,
            MetricSeries(
                metric_name="bar",
                metric_type=MetricType.COUNT.name,
                series=[(1, (1681171200, "foo")), (1, (1681257600, "foo"))],
                columns=["timestamp", "function_path"],
            ),
        ),
        (
            MetricsFilter(
                name="bar",
                from_time=datetime.datetime.fromtimestamp(0),
                to_time=datetime.datetime.utcnow(),
                labels={},
            ),
            [],
            "auto",
            MetricSeries(
                metric_name="bar",
                metric_type=MetricType.COUNT.name,
                series=[(1, (1681171200,)), (1, (1681257600,))],
                columns=["timestamp"],
            ),
        ),
    ),
)
def test_get_aggregated_metrics(
    metrics_filter: MetricsFilter,
    group_by: List[GroupBy],
    rollup: Union[int, Literal["auto"], None],
    expected_series: MetricSeries,
    test_db: DB,  # noqa: F811
    metric_points: List[MetricPoint],
):
    metrics_storage_plugin = SQLMetricsStorage()
    metrics_storage_plugin.store_metrics(metric_points)

    metric_series = metrics_storage_plugin.get_aggregated_metrics(
        filter=metrics_filter,
        group_by=group_by,
        rollup=rollup,
    )

    assert metric_series == expected_series


@pytest.mark.parametrize(
    "rollup, expected_series_length, expected_series_first_value",
    (("auto", 251, 3.0), (100, 11, 99.0), (20, 51, 19.0), (None, 1, 1000)),
)
def test_get_aggregated_metrics_rollup(
    rollup,
    expected_series_length,
    expected_series_first_value,
    test_db: DB,  # noqa: F811
):
    metric_points = [
        MetricPoint(
            name="foo",
            metric_type=MetricType.COUNT,
            value=1,
            labels={},
            metric_time=datetime.datetime.fromtimestamp(i + 1),
        )
        for i in range(1000)
    ]

    metrics_storage_plugin = SQLMetricsStorage()
    metrics_storage_plugin.store_metrics(metric_points)

    metric_series = metrics_storage_plugin.get_aggregated_metrics(
        filter=MetricsFilter(
            name="foo",
            from_time=datetime.datetime.fromtimestamp(0),
            to_time=datetime.datetime.fromtimestamp(1001),
            labels={},
        ),
        group_by=[],
        rollup=rollup,
    )

    assert len(metric_series.series) == expected_series_length
    assert metric_series.series[0][0] == expected_series_first_value


def test_clear_metrics(
    test_db: DB,  # noqa: F811
    metric_points: List[MetricPoint],
):
    metrics_storage_plugin = SQLMetricsStorage()
    metrics_storage_plugin.store_metrics(metric_points)

    metrics_storage_plugin.clear_metrics(
        MetricsFilter(
            name="foo",
            from_time=datetime.datetime.fromtimestamp(0),
            to_time=datetime.datetime.utcnow(),
            labels={"function_path": "foo"},
        )
    )

    with test_db.get_session() as session:
        metric_label_count = session.query(MetricLabel).count()
        metric_value_count = session.query(MetricValue).count()

    assert metric_label_count == 3
    assert metric_value_count == 3
