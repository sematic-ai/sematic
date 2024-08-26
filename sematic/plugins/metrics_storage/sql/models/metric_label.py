# Third-party
from sqlalchemy import Index, types
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

# Sematic
from sematic.db.models.base import Base
from sematic.db.models.mixins.has_organization_mixin import HasOrganizationMixin
from sematic.metrics.metric_point import MetricsLabels, MetricType
from sematic.utils.db import IntEnum


class MetricLabel(HasOrganizationMixin, Base):
    """
    A unique set of labels for a given metric name.

    Schema inspired by
    https://github.com/CrunchyData/postgresql-prometheus-adapter/blob/main/pkg/postgresql/client.go

    Parameters
    ----------
    metric_id: str
        A unique ID for this metric name and set of labels.
    metric_name: str
        The metric name.
    metric_labels: MetricLabels
        A key/value dictionary of labels.
    metric_type: MetricType
        The metric's type.
    organization_id: Optional[str]
        The organization under which this resolution was submitted.
    """

    __tablename__ = "metric_labels"

    metric_id: Mapped[str] = mapped_column(
        types.String(), nullable=False, primary_key=True
    )
    metric_name: Mapped[str] = mapped_column(types.String(), nullable=False)
    metric_labels: Mapped[MetricsLabels] = mapped_column(JSONB(), nullable=False)
    metric_type: Mapped[MetricType] = mapped_column(IntEnum(MetricType), nullable=False)

    __table_args__ = (
        Index(
            "metric_labels_name_labels_idx", "metric_name", "metric_labels", unique=True
        ),
    )
