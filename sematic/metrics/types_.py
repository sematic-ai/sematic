# Standard Library
import enum
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, Union


class MetricType(enum.IntEnum):
    COUNT = 0  # Aggregation by sum
    GAUGE = 1  # Aggregation by mean or median (ref)
    HISTOGRAM = 2  # Aggregation by counts in buckets


class MetricScope(enum.IntEnum):
    RUN = 0
    PIPELINE = 1
    ORGANIZATION = 2


@dataclass
class MetricPoint:
    name: str
    value: float
    metric_type: MetricType
    labels: Dict[str, Union[int, float, str, bool, None]]
    metric_time: datetime

    def to_json_encodable(self) -> Dict[str, Any]:
        output = asdict(self)
        output["metric_type"] = self.metric_type.value
        return output

    @classmethod
    def from_json_encodable(cls, payload: Dict[str, Any]) -> "MetricPoint":
        payload["metric_type"] = MetricType(payload["metric_type"])
        return cls(**payload)
