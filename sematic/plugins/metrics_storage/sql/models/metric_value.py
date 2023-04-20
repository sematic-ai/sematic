# Standard Library
import datetime

# Third-party
from sqlalchemy import Column, ForeignKey, types

# Sematic
from sematic.db.models.base import Base
from sematic.plugins.metrics_storage.sql.models.metric_label import MetricLabel


class MetricValue(Base):
    """
    A metric value.

    Schema inspired by
    https://github.com/CrunchyData/postgresql-prometheus-adapter/blob/main/pkg/postgresql/client.go

    Parameters
    ----------
    metric_id: str
        Foreign key to metric_label.metric_id.
    value: float
        The value to store.
    metric_time: datetime
        The time at which the value was recorded.
    """

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
