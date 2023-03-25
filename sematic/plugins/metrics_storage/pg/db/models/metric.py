# Standard Library
import datetime
from typing import Any

# Third-party
from sqlalchemy import Column, types

# Sematic
from sematic.db.models.base import Base
from sematic.plugins.abstract_metrics_storage import (
    MetricScope,
    MetricType,
    MetricValue,
)


class Metric(Base):
    __tablename__ = "metrics"

    name: str = Column(types.String(), nullable=False)
    value: MetricValue = Column(types.JSON(), nullable=False)
    scope: MetricScope = Column(types.String(), nullable=False)  # type: ignore
    scope_id: str = Column(types.String(), nullable=False)
    metric_type: MetricType = Column(types.String(), nullable=False)  # type: ignore
    measured_at: int = Column(types.Integer(), nullable=False)
    annotations: Any = Column(types.JSON(), default=dict)
    created_at: datetime.datetime = Column(
        types.DateTime(), nullable=False, default=datetime.datetime.utcnow
    )
