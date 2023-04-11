# Standard Library
import enum
import logging
from typing import Dict, List, Optional, Type

# Sematic
from sematic.abstract_metric import AbstractMetric
from sematic.db.models.run import Run
from sematic.db.models.user import User
from sematic.metrics.func_effective_runtime import FuncEffectiveRuntime
from sematic.metrics.func_run_count import FuncRunCount
from sematic.metrics.func_success_rate import FuncSuccessRate
from sematic.metrics.types_ import MetricPoint
from sematic.plugins.abstract_metrics_storage import get_metrics_storage_plugins
from sematic.plugins.metrics_storage.pg.pg_metrics_storage import PGMetricsStorage

logger = logging.getLogger(__name__)


class MetricEvent(enum.IntEnum):
    run_future_state_changed = 0
    run_created = 1


_METRICS: Dict[MetricEvent, List[Type[AbstractMetric]]] = {
    MetricEvent.run_created: [
        FuncRunCount,
    ],
    MetricEvent.run_future_state_changed: [
        FuncSuccessRate,
        FuncEffectiveRuntime,
    ],
}


def save_event_metrics(
    event: MetricEvent, runs: List[Run], user: Optional[User] = None
):
    if len(runs) == 0:
        return

    for plugin_class in get_metrics_storage_plugins(default=[PGMetricsStorage]):
        logging.info("Saving metrics to %s", plugin_class.get_path())  # type: ignore

        metric_points: List[MetricPoint] = []

        for metric_class in _METRICS[event]:
            metric = metric_class()
            for run in runs:
                metric_point = metric.make_metric_point(run)

                if metric_point is None:
                    continue

                logging.info("Saving metric %s", metric.get_full_name())

                metric_points.append(metric_point)

        plugin_class().store_metrics(metric_points)
