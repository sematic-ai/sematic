# Standard Library
import abc
import enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Iterable, List, Optional, Tuple, Type, Union, cast

# Sematic
from sematic.abstract_plugin import AbstractPlugin, PluginScope
from sematic.config.settings import get_active_plugins
from sematic.metrics.types_ import MetricPoint

MetricsLabels = Dict[str, Union[int, float, str, bool, None]]


@dataclass
class MetricsFilter:
    name: str
    from_time: datetime
    to_time: datetime
    labels: MetricsLabels


@dataclass
class MetricSeries:
    metric_name: str
    metric_type: Optional[str] = None
    series: List[Tuple[float, Tuple[str, ...]]] = field(default_factory=list)
    group_by_labels: List[str] = field(default_factory=list)


class GroupBy(enum.Enum):
    timestamp = "timestamp"
    date = "date"
    run_id = "run_id"
    calculator_path = "calculator_path"
    root_id = "root_id"
    root_calculator_path = "root_calculator_path"


class NoMetricError(Exception):
    def __init__(self, metric_name: str, plugin_name: str):
        super().__init__(f"No metric named {metric_name} was found in {plugin_name}")


class AbstractMetricsStorage(abc.ABC):
    @abc.abstractmethod
    def store_metrics(self, metric: List[MetricPoint]) -> None:
        # Stores the data points in the plugin's data store
        pass

    @abc.abstractmethod
    def get_metrics(self, filter: MetricsFilter) -> Iterable[MetricPoint]:
        # Returns a list of unaggregated data points
        pass

    @abc.abstractmethod
    def get_aggregated_metrics(
        self, filter: MetricsFilter, group_by: List[GroupBy]
    ) -> MetricSeries:
        # Returns a compact payload of aggregated metrics for display in the dashboard
        pass

    @abc.abstractmethod
    def clear_metrics(self, filter: MetricsFilter) -> None:
        # Necessary to clear metrics upon run retries
        pass


def get_metrics_storage_plugins(
    default: List[Type[AbstractPlugin]],
) -> List[Type[AbstractMetricsStorage]]:
    """
    Return all configured "METRICS_STORAGE" scope plugins.
    """
    storage_plugins = get_active_plugins(PluginScope.METRICS_STORAGE, default=default)

    storage_classes = [
        cast(Type[AbstractMetricsStorage], plugin) for plugin in storage_plugins
    ]

    return storage_classes
