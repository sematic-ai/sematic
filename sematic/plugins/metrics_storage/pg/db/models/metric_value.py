# Standard Library
import datetime

# Third-party
from sqlalchemy import Column, ForeignKey, types

# Sematic
from sematic.db.models.base import Base
from sematic.plugins.metrics_storage.pg.db.models.metric_label import MetricLabel


class MetricValue(Base):
    __tablename__ = "metric_values"

    metric_id: str = Column(
        types.String(),
        ForeignKey(MetricLabel.metric_id),
        nullable=False,
        primary_key=True,
    )
    value: float = Column(types.Float(), nullable=False)
    metric_time: datetime.datetime = Column(
        types.DateTime(), nullable=False, primary_key=True
    )
    created_at: datetime.datetime = Column(
        types.DateTime(), nullable=False, default=datetime.datetime.utcnow
    )
