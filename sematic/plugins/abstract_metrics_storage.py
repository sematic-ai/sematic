# Standard Library
import abc
import enum
import numbers
from dataclasses import dataclass
from typing import Dict, List, Optional, Union


class MetricType(enum.Enum):
    COUNT = 0  # Aggregation by sum
    GAUGE = 1  # Aggregation by mean or median (ref)
    HISTOGRAM = 2  # Aggregation by counts in buckets


class MetricScope(enum.Enum):
    RUN = 0
    PIPELINE = 1
    ORGANIZATION = 2


MetricScalar = Union[int, float, str, bool, None]
MetricValue = Dict[str, MetricScalar]


@dataclass
class MetricPoint:
    name: str
    value: MetricValue
    metric_type: MetricType
    scope: MetricScope
    scope_id: str
    annotations: Dict[str, Union[numbers.Real, str, bool, None]]
    measured_at: int


@dataclass
class MetricsFilter:
    scope: MetricScope
    scope_id: str  # run_id, calculator_path, organization_id depending on scope
    name: Optional[str]
    from_time: int
    to_time: int


@dataclass
class AggregationOptions:
    timeseries_buckets: Optional[str]


@dataclass
class AggregatedMetricsBucket:
    from_time: int
    to_time: int
    aggregations: Dict[str, Dict[str, numbers.Real]]


@dataclass
class AggregatedMetrics:
    filters: MetricsFilter
    totals: AggregatedMetricsBucket
    buckets: List[AggregatedMetricsBucket]
    options: Optional[AggregationOptions] = None


class AbstractMetricsStorage(abc.ABC):
    @abc.abstractmethod
    def store_metrics(self, metric: List[MetricPoint]) -> None:
        # Stores the data points in the plugin's data store
        pass

    @abc.abstractmethod
    def get_metrics(self, filters: MetricsFilter) -> List[MetricPoint]:
        # Returns a list of unaggregated data points
        pass

    @abc.abstractmethod
    def get_aggregated_metrics(
        self, filters: MetricsFilter, options: Optional[AggregationOptions] = None
    ) -> AggregatedMetrics:
        # Returns a compact payload of aggregated metrics for display in the dashboard
        pass

    @abc.abstractmethod
    def clear_metrics(self, scope: MetricScope, scope_id: str) -> None:
        # Necessary to clear metrics upon run retries
        pass
