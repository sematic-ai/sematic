# Standard Library
from datetime import datetime
from typing import Any, Dict
from unittest import mock

# Third-party
import pytest

# Sematic
from sematic.ee.metrics import MetricScope, log_metric
from sematic.future_context import PrivateContext, SematicContext
from sematic.metrics.metric_point import MetricPoint, MetricType
from sematic.utils.exceptions import NotInSematicFuncError


@pytest.mark.parametrize(
    "kwargs",
    (
        (
            dict(name="my_metric", value=42.0),
            dict(name="my_metric", value=42.0, metric_type=MetricType.COUNT),
            dict(name="my_metric", value=42.0, scope=MetricScope.PIPELINE),
        )
    ),
)
@mock.patch("sematic.ee.metrics.api_client.save_metric_points")
@mock.patch(
    "sematic.ee.metrics.context",
    return_value=SematicContext(
        run_id="foo", root_id="bar", private=PrivateContext(resolver_class_path="bat")
    ),
)
@mock.patch("sematic.ee.metrics._get_function_path", return_value="function_path")
@mock.patch("sematic.ee.metrics.datetime")
def test_log_metric(
    mock_datetime: mock.MagicMock,
    mock_get_function_path: mock.MagicMock,
    mock_context: mock.MagicMock,
    mock_save_metric_points: mock.MagicMock,
    kwargs: Dict[str, Any],
):
    mock_datetime.utcnow.return_value = datetime.fromtimestamp(0)
    log_metric(**kwargs)

    mock_save_metric_points.assert_called_with(
        [
            MetricPoint(
                name=kwargs["name"],
                value=kwargs["value"],
                metric_time=datetime.fromtimestamp(0),
                metric_type=kwargs.get("metric_type", MetricType.GAUGE),
                labels={
                    "__scope__": kwargs.get("scope", MetricScope.RUN.value),
                    "run_id": "foo",
                    "function_path": "function_path",
                    "root_id": "bar",
                    "root_function_path": "function_path",
                },
            )
        ]
    )


def test_log_metric_no_context():
    with pytest.raises(
        NotInSematicFuncError,
        match="log_metric must be called within a Sematic Function.",
    ):
        log_metric("foo", 1.0)
