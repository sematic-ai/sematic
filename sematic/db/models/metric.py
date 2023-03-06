# Standard Library
import datetime
import enum
from typing import Any, Dict

# Third-party
from sqlalchemy import Column, types

# Sematic
from sematic.db.models.base import Base
from sematic.db.models.mixins.json_encodable_mixin import JSONEncodableMixin


class MetricScope(enum.Enum):
    RUN = "RUN"
    PIPELINE = "PIPELINE"


class Metric(Base, JSONEncodableMixin):

    __tablename__ = "metrics"

    name: str = Column(types.String(), nullable=False)
    value: float = Column(types.Float(), nullable=False)

    run_id: str = Column(types.String(), nullable=False, primary_key=True)
    root_id: str = Column(types.String(), nullable=False)

    scope: str = Column(types.String(), nullable=False)

    # 'metadata' is reserved by SQLAlchemy
    annotations: Dict[str, Any] = Column(types.JSON(), nullable=False, default=dict)

    created_at: datetime.datetime = Column(
        types.DateTime(),
        nullable=False,
        default=datetime.datetime.utcnow,
        primary_key=True,
    )
