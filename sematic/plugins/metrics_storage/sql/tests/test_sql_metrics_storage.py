# Standard Library
import datetime
from typing import List

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
            labels=dict(calculator_path="foo"),
        ),
        MetricPoint(
            name="foo",
            value=0,
            metric_type=MetricType.GAUGE,
            metric_time=datetime.datetime(2023, 4, 11),
            labels=dict(calculator_path="bar"),
        ),
        MetricPoint(
            name="bar",
            value=1,
            metric_type=MetricType.COUNT,
            metric_time=datetime.datetime(2023, 4, 12),
            labels=dict(calculator_path="foo"),
        ),
        MetricPoint(
            name="bar",
            value=1,
            metric_type=MetricType.COUNT,
            metric_time=datetime.datetime(2023, 4, 11),
            labels=dict(calculator_path="foo"),
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
    "metrics_filter, group_by, expected_series",
    (
        (
            MetricsFilter(
                name="foo",
                from_time=datetime.datetime.fromtimestamp(0),
                to_time=datetime.datetime.utcnow(),
                labels={},
            ),
            [],
            MetricSeries(
                metric_name="foo",
                metric_type=MetricType.GAUGE.name,
                series=[(0.5, ())],
                group_by_labels=[],
            ),
        ),
        (
            MetricsFilter(
                name="foo",
                from_time=datetime.datetime.fromtimestamp(0),
                to_time=datetime.datetime.utcnow(),
                labels={},
            ),
            [GroupBy.date],
            MetricSeries(
                metric_name="foo",
                metric_type=MetricType.GAUGE.name,
                series=[(0, ("2023-04-11",)), (1, ("2023-04-12",))],
                group_by_labels=["date"],
            ),
        ),
        (
            MetricsFilter(
                name="foo",
                from_time=datetime.datetime.fromtimestamp(0),
                to_time=datetime.datetime.utcnow(),
                labels={"calculator_path": "foo"},
            ),
            [GroupBy.calculator_path],
            MetricSeries(
                metric_name="foo",
                metric_type=MetricType.GAUGE.name,
                series=[(1, ("foo",))],
                group_by_labels=["calculator_path"],
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
            MetricSeries(
                metric_name="bar",
                metric_type=MetricType.COUNT.name,
                series=[(2, ())],
                group_by_labels=[],
            ),
        ),
        (
            MetricsFilter(
                name="bar",
                from_time=datetime.datetime.fromtimestamp(0),
                to_time=datetime.datetime.utcnow(),
                labels={},
            ),
            [GroupBy.date, GroupBy.calculator_path],
            MetricSeries(
                metric_name="bar",
                metric_type=MetricType.COUNT.name,
                series=[(1, ("2023-04-11", "foo")), (1, ("2023-04-12", "foo"))],
                group_by_labels=["date", "calculator_path"],
            ),
        ),
    ),
)
def test_get_aggregated_metrics(
    metrics_filter: MetricsFilter,
    group_by: List[GroupBy],
    expected_series: MetricSeries,
    test_db: DB,  # noqa: F811
    metric_points: List[MetricPoint],
):
    metrics_storage_plugin = SQLMetricsStorage()
    metrics_storage_plugin.store_metrics(metric_points)

    metric_series = metrics_storage_plugin.get_aggregated_metrics(
        filter=metrics_filter,
        group_by=group_by,
    )

    assert metric_series == expected_series


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
            labels={"calculator_path": "foo"},
        )
    )

    with test_db.get_session() as session:
        metric_label_count = session.query(MetricLabel).count()
        metric_value_count = session.query(MetricValue).count()

    assert metric_label_count == 3
    assert metric_value_count == 3
