# Standard Library
import datetime
from typing import Any, List

# Third-party
import pytest

# Sematic
from sematic.db.db import DB
from sematic.db.tests.fixtures import test_db  # noqa: F401
from sematic.metrics.metric_point import MetricPoint, MetricType
from sematic.plugins.metrics_storage.sql.sql_metrics_storage import SQLMetricsStorage

EPSILON = 0.00001


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


# In reality: a 2 element list where the first element is a float value,
# and the second element is a list of string labels
SeriesPoint = Any


def check_approximate_equality(a: List[SeriesPoint], b: List[SeriesPoint]):
    assert len(a) == len(b)
    for a_row, b_row in zip(a, b):
        assert len(a_row) == 2
        assert len(b_row) == 2
        a_value, a_labels = a_row
        b_value, b_labels = b_row
        assert_approx_equal_floats(a_value, b_value)

        for a_label, b_label in zip(a_labels, b_labels):
            assert isinstance(
                a_label, str
            ), f"First series contained non-string label: {a_label}"
            assert isinstance(
                b_label, str
            ), f"Second series contained non-string label: {b_label}"
            if is_float_str(a_label):
                assert_approx_equal_floats(float(a_label), float(b_label))
            else:
                assert a_label == b_label


def is_float_str(x: str):
    try:
        float(x)
        return True
    except (TypeError, ValueError):
        return False


def assert_approx_equal_floats(a: float, b: float):
    if a == 0 and b == 0:
        return
    assert abs(a - b) / (2 * (abs(a) + abs(b))) < EPSILON
