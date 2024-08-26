# Standard Library
import datetime

# Third-party
from sqlalchemy import ForeignKey, Index, types
from sqlalchemy.orm import Mapped, mapped_column

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

    metric_id: Mapped[str] = mapped_column(
        types.String(),
        ForeignKey(MetricLabel.metric_id),
        nullable=False,
        primary_key=True,
    )
    value: Mapped[float] = mapped_column(types.Float(), nullable=False)
    metric_time: Mapped[datetime.datetime] = mapped_column(
        types.DateTime(), nullable=False, primary_key=True
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        types.DateTime(), nullable=False, default=datetime.datetime.utcnow
    )


Index(
    "metric_values_id_time_idx", MetricValue.metric_id, MetricValue.metric_time.desc()
),
Index("metric_values_time_idx", MetricValue.metric_time.desc())
