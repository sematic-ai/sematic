# Standard Library
import enum
from datetime import datetime
from typing import Dict

# Sematic
import sematic.api_client as api_client
from sematic.future_context import NotInSematicFuncError, context
from sematic.metrics.metric_point import MetricPoint, MetricType


class MetricScope(enum.Enum):
    RUN = "0"
    PIPELINE = "1"
    # ORGANIZATION = 2


def log_metric(
    name: str,
    value: float,
    scope: MetricScope = MetricScope.RUN,
    metric_type: MetricType = MetricType.GAUGE,
) -> None:
    """
    Log a metric value.

    Parameters
    ----------
    name: str
        The name of the metric for which to log a value.
    value: float
        The value to log.
    scope: MetricScope
        One of MetricScope.RUN, MetricScope.PIPELINE. Defaults to
        MetricScope.RUN. When MetricScope.RUN, the plot for this metric will be
        displayed in the Metrics tab of the current run. When
        MetricScope.PIPELINE, the plot for this metric will be displayed in the
        Pipeline Metrics panel.
    metric_type: MetricType
        One of MetricType.GAUGE, MetricType.COUNT. Defaults to MetricType.GAUGE.
        When MetricType.COUNT, values are aggregated by sum. When
        MetricType.GAUGE, metric values are aggregated by average.
    """
    try:
        run_id, root_id = context().run_id, context().root_id
    except NotInSematicFuncError:
        raise NotInSematicFuncError(
            "log_metric must be called within a Sematic Function."
        )

    metric_point = MetricPoint(
        name=name,
        value=value,
        metric_time=datetime.utcnow(),
        metric_type=metric_type,
        labels={
            "__scope__": scope.value,
            "run_id": run_id,
            "function_path": _get_function_path(run_id),
            "root_id": root_id,
            "root_function_path": _get_function_path(root_id),
        },
    )

    api_client.save_metric_points([metric_point])


_FUNCTION_PATH_CACHE: Dict[str, str] = {}


def _get_function_path(run_id: str) -> str:
    if run_id not in _FUNCTION_PATH_CACHE:
        _FUNCTION_PATH_CACHE[run_id] = api_client.get_run(run_id).function_path

    return _FUNCTION_PATH_CACHE[run_id]
