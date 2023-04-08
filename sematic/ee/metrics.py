# Standard Library
import datetime
from typing import Dict

# Sematic
import sematic.api_client as api_client
from sematic.future_context import context
from sematic.metrics.types_ import MetricPoint, MetricScope, MetricType


def log_metric(
    name: str,
    value: float,
    scope: MetricScope = MetricScope.RUN,
    metric_type: MetricType = MetricType.GAUGE,
) -> None:
    run_id, root_id = context().run_id, context().root_id

    metric_point = MetricPoint(
        name=name,
        value=value,
        metric_time=datetime.datetime.utcnow(),
        metric_type=metric_type,
        labels={
            "__scope__": scope.value,
            "run_id": run_id,
            "calculator_path": _get_calculator_path(run_id),
            "root_id": root_id,
            "root_calculator_path": _get_calculator_path(root_id),
        },
    )

    api_client.save_metric_points([metric_point])


_CACHE: Dict[str, str] = {}


def _get_calculator_path(run_id: str) -> str:
    if run_id not in _CACHE:
        _CACHE[run_id] = api_client.get_run(run_id).calculator_path

    return _CACHE[run_id]
