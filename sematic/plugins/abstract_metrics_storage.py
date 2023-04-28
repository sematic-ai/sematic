"""
Module declaring the interface for metrics storage plug-ins.
"""
# Standard Library
import abc
import enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Literal, Optional, Sequence, Tuple, Type, Union, cast

# Sematic
from sematic.abstract_plugin import AbstractPlugin, PluginScope
from sematic.config.settings import get_active_plugins
from sematic.metrics.metric_point import MetricPoint, MetricsLabels


@dataclass
class MetricsFilter:
    """
    Data structure to query metrics.
    """

    name: str
    from_time: datetime
    to_time: datetime
    labels: MetricsLabels


@dataclass
class MetricSeries:
    """
    Data structure to represent a metric series for queries to return.

    Series are typically aggregated by labels.

    Parameters
    ----------
    metric_name: str
        The name of the metric
    metric_type: str
        One of `MetricType`. Using the str value instead of Enum instance for
        serializability.
    series: List[Tuple[float, Tuple[str, ...]]]
        The metric series. A list of tuples. Every element in the list
        corresponds to a series value. The tuple contains two elements: the
        value, and a tuple of label values. The order of label values
        corresponds to the order of label names in columns.
    columns: List[str]
        The list of label names the metric was aggregated over.

    Examples
    --------
    Run count with no aggregations:
    ```
    MetricSeries(
        metric_name="sematic.func_run_count",
        metric_type="COUNT",
        series=[(483.0, ())],
        columns=[],
    )
    ```

    Success rate by calculator path by day:
    ```
    MetricSeries(
        metric_name="sematic.func_success_rate",
        metric_type="GAUGE",
        series=[
            (0.68, ("path.to.foo", "2023-04-12")),
            (0.95, ("path.to.foo", "2023-04-11")),
            (0.45, ("path.to.bar", "2023-04-12")),
            ...
        ],
        columns=["calculator_path", "date"],
    )
    ```
    """

    metric_name: str
    metric_type: Optional[str] = None
    series: List[Tuple[float, Tuple[Union[str, int], ...]]] = field(
        default_factory=list
    )
    columns: List[str] = field(default_factory=list)


class GroupBy(enum.Enum):
    """
    Options to aggregate metrics over.
    """

    run_id = "run_id"
    function_path = "function_path"
    root_id = "root_id"
    root_function_path = "root_function_path"


RollUp = Union[int, Literal["auto"], None]


class NoMetricError(Exception):
    def __init__(self, metric_name: str, plugin_name: str):
        super().__init__(f"No metric named {metric_name} was found in {plugin_name}")


class AbstractMetricsStorage(abc.ABC):
    """
    Abstract base class for metrics storage plug-ins.
    """

    @abc.abstractmethod
    def store_metrics(self, metric_points: Sequence[MetricPoint]) -> None:
        """
        Persists a list of metric points.

        Parameters
        ----------
        metric_points: Iterable[MetricPoint]
            List of metric points to persist.
        """
        pass

    @abc.abstractmethod
    def get_metrics(self, labels: MetricsLabels) -> Tuple[str, ...]:
        """
        Gets the list of unique metric names for the given set of labels.

        Parameters
        ----------
        labels: MetricsLabels
            Labels by which to filter metric names.
        """
        pass

    @abc.abstractmethod
    def get_aggregated_metrics(
        self,
        filter: MetricsFilter,
        group_by: Sequence[GroupBy],
        rollup: RollUp,
    ) -> MetricSeries:
        """
        Returns a metric aggregation according to the provided filter and group
        bys.

        Parameters
        ----------
        filter: MetricsFilter
            Criteria to filter metrics values.
        group_by: Iterable[GroupBy]
            List of dimensions to aggregate metrics over.
        rollup: RollUp
            How to aggregate metrics over time. `None` means no aggregation,
            returns a single scalar per combination of `group_by` dimensions.
            `"auto"` means the optimal aggregation interval will be found to
            have a maximum of 300 series points. Passing an int sets the
            interval size in seconds. If this interval is capped to yield no
            more than 300 buckets.

        Examples
        --------
        All time run count:
        ```
        MetricsStorage().get_aggregated_metrics(
            filter=MetricsFilter(
                name="sematic.func_run_count",
                from_time=datetime.fromtimestamp(0), to_time=datetime.utcnow(),
                labels={}
            ), group_by=[], rollup=None,
        )
        ```

        Success rate for Function `path.to.foo` by date over the last 30 days:
        ```
        MetricsStorage().get_aggregated_metrics(
            filter=MetricsFilter(
                name="sematic.func_run_count", from_time=(datetime.utcnow() -
                datetime.timedelta(days=30)), to_time=datetime.utcnow(),
                labels={"calculator_path": "path.to.foo"}
            ), group_by=[], rollup=24 * 3600,
        )
        ```
        """
        pass

    @abc.abstractmethod
    def clear_metrics(self, filter: MetricsFilter) -> None:
        """
        Delete metrics values corresponding to a given filter.

        This is useful for retried processes.
        """
        pass


def get_metrics_storage_plugins(
    default: List[Type[AbstractPlugin]],
) -> List[Type[AbstractMetricsStorage]]:
    """
    Return all configured metrics plug-ins for scope.
    """
    storage_plugins = get_active_plugins(PluginScope.METRICS_STORAGE, default=default)

    storage_classes = [
        cast(Type[AbstractMetricsStorage], plugin) for plugin in storage_plugins
    ]

    return storage_classes
