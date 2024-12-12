# Standard Library
import datetime
from typing import List, Literal, Union

# Third-party
import pytest

# Sematic
from sematic.db.db import DB
from sematic.db.tests.fixtures import test_db  # noqa: F401
from sematic.metrics.metric_point import MetricPoint, MetricType
from sematic.metrics.tests.fixtures import (  # noqa: F401
    check_approximate_equality,
    metric_points,
)
from sematic.plugins.abstract_metrics_storage import (
    GroupBy,
    MetricSeries,
    MetricsFilter,
)
from sematic.plugins.metrics_storage.sql.models.metric_label import MetricLabel
from sematic.plugins.metrics_storage.sql.models.metric_value import MetricValue
from sematic.plugins.metrics_storage.sql.sql_metrics_storage import SQLMetricsStorage


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
                series=[(0, (str(1681171200),)), (1, (str(1681257600),))],
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
                series=[(1, (str(1681171200), "foo")), (1, (str(1681257600), "foo"))],
                columns=["timestamp", "function_path"],
            ),
        ),
        (
            MetricsFilter(
                name="bar",
                from_time=datetime.datetime.fromtimestamp(0),
                to_time=datetime.datetime.utcnow() + datetime.timedelta(days=1),
                labels={},
            ),
            [],
            "auto",
            MetricSeries(
                metric_name="bar",
                metric_type=MetricType.COUNT.name,
                series=[(1, (str(1681171200),)), (1, (str(1681257600),))],
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
    metric_points: List[MetricPoint],  # noqa: F811
):
    metrics_storage_plugin = SQLMetricsStorage()
    metrics_storage_plugin.store_metrics(metric_points)

    metric_series = metrics_storage_plugin.get_aggregated_metrics(
        filter=metrics_filter,
        group_by=group_by,
        rollup=rollup,
    )
    assert isinstance(metric_series, MetricSeries)
    assert metric_series.metric_name == expected_series.metric_name
    assert metric_series.metric_type == expected_series.metric_type
    assert metric_series.columns == expected_series.columns

    check_approximate_equality(
        metric_series.series, expected_series.series, equality_epsilon=24 * 3600
    )


@pytest.mark.parametrize(
    "rollup, expected_series_length, expected_series_first_value",
    [("auto", 251, 3.0), (100, 11, 99.0), (20, 51, 19.0), (None, 1, 1000)],
)
def test_get_aggregated_metrics_rollup(
    rollup,
    expected_series_length,
    expected_series_first_value,
    test_db: DB,  # noqa: F811
):
    metric_points = [  # noqa: F811
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

    assert abs(len(metric_series.series) - expected_series_length) <= 1
    assert sum(val[0] for val in metric_series.series) == 1000


def test_clear_metrics(
    test_db: DB,  # noqa: F811
    metric_points: List[MetricPoint],  # noqa: F811
):
    metrics_storage_plugin = SQLMetricsStorage()
    metrics_storage_plugin.store_metrics(metric_points)

    with test_db.get_session() as session:
        initial_metric_value_count = session.query(MetricValue).count()

    metrics_storage_plugin.clear_metrics(
        MetricsFilter(
            name="foo",
            from_time=datetime.datetime.fromtimestamp(0),
            to_time=datetime.datetime.utcnow() + datetime.timedelta(days=1),
            labels={},
        )
    )

    with test_db.get_session() as session:
        metric_value_count = session.query(MetricValue).count()

    assert metric_value_count < initial_metric_value_count
