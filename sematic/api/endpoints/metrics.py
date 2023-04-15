# Standard Library
import enum
import logging
from typing import Dict, List, Optional, Type

# Sematic
from sematic.abstract_metric import AbstractMetric
from sematic.abstract_plugin import PluginScope
from sematic.db.models.run import Run
from sematic.db.models.user import User
from sematic.metrics.func_run_count import FuncRunCount
from sematic.metrics.metric_point import MetricPoint
from sematic.plugins.abstract_metrics_storage import get_metrics_storage_plugins
from sematic.plugins.metrics_storage.sql.sql_metrics_storage import SQLMetricsStorage

logger = logging.getLogger(__name__)


class MetricEvent(enum.IntEnum):
    run_created = 1


_METRICS: Dict[MetricEvent, List[Type[AbstractMetric]]] = {
    MetricEvent.run_created: [
        FuncRunCount,
    ],
}


def save_event_metrics(
    event: MetricEvent, runs: List[Run], user: Optional[User] = None
):
    if len(runs) == 0:
        return

    metric_points: List[MetricPoint] = []

    for metric_class in _METRICS[event]:
        metric = metric_class()
        for run in runs:
            metric_point = metric.make_metric_point(run, user)

            if metric_point is None:
                continue

            logging.info(
                "Generated metric %s for run %s with value %s",
                metric.get_full_name(),
                run.id,
                metric_point.value,
            )

            metric_points.append(metric_point)

    for plugin_class in get_metrics_storage_plugins(
        PluginScope.METRICS_WRITE, default=[SQLMetricsStorage]
    ):
        logging.info("Saving metrics to %s", plugin_class.get_path())  # type: ignore
        plugin_class().store_metrics(metric_points)
