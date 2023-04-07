# Standard Library
from typing import Dict, Union

# Third-party
from sqlalchemy import Column, types
from sqlalchemy.dialects.postgresql import JSONB

# Sematic
from sematic.db.models.base import Base
from sematic.metrics.types_ import MetricType
from sematic.utils.db import IntEnum


class MetricLabel(Base):
    __tablename__ = "metric_labels"

    metric_id: str = Column(types.String(), nullable=False, primary_key=True)
    metric_name: str = Column(types.String(), nullable=False)
    metric_labels: Dict[str, Union[int, float, str, bool, None]] = Column(
        JSONB(), nullable=False
    )
    metric_type: MetricType = Column(IntEnum(MetricType), nullable=False)

    def __hash__(self) -> int:
        return hash(self.metric_id)
