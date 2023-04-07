# Standard Library
import enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional, Tuple, Union


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
