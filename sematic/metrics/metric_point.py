# Standard Library
import enum
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, Union


class MetricType(enum.IntEnum):
    """
    A metric's type dictates how it gets aggregated.
    See https://opentelemetry.io/docs/reference/specification/metrics/data-model/#timeseries-model  # noqa: E501
    """

    COUNT = 0  # Aggregation by sum
    GAUGE = 1  # Aggregation by average
    # Unsupported yet
    # HISTOGRAM = 2  # Aggregation by counts in buckets


MetricsLabels = Dict[str, Union[int, float, str, bool, None]]


@dataclass(frozen=True)
class MetricPoint:
    """
    A data structure to represent a single metric value.

    Parameters
    ----------
    name: str
        The metric name.
    value: float
        The metric value.
    metric_type: MetricType
        The metric type dictates how it gets aggregated. See Metric Type.
    labels: MetricsLabels
        A dictionary of label names to values for this metric point.
    metric_time: datetime
        The time at which this value was recorded.
    """

    name: str
    value: float
    metric_type: MetricType
    labels: MetricsLabels
    metric_time: datetime

    def to_json_encodable(self) -> Dict[str, Any]:
        output = asdict(self)
        output["metric_type"] = self.metric_type.value
        output["metric_time"] = self.metric_time.timestamp()
        return output

    @classmethod
    def from_json_encodable(cls, payload: Dict[str, Any]) -> "MetricPoint":
        payload["metric_type"] = MetricType(payload["metric_type"])
        payload["metric_time"] = datetime.fromtimestamp(payload["metric_time"])
        return cls(**payload)
