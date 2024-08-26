# Standard Library
import datetime
import uuid
from typing import Optional

# Third-party
from sqlalchemy import types
from sqlalchemy.orm import Mapped, mapped_column

# Sematic
from sematic.db.models.base import Base
from sematic.db.models.mixins.json_encodable_mixin import JSONEncodableMixin


class Organization(Base, JSONEncodableMixin):
    """
    SQLAlchemy model for Organizations.

    Attributes
    ----------
    id: str
        The ID of the organization. Defaults to a random UUID.
    name: str
        A human-readable name for the Organization.
    kubernetes_namespace: Optional[str]
        The Kubernetes namespace in which this Organization can submit workloads. Defaults
        to `None`, meaning the Server namespace.
    created_at: datetime.datetime
        The creation time. Defaults to the current time.
    updated_at: datetime.datetime
        The last update time. Auto-updates to the current time.
    """

    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(
        types.String(), primary_key=True, default=lambda: uuid.uuid4().hex
    )
    name: Mapped[str] = mapped_column(types.String(), nullable=False)
    kubernetes_namespace: Mapped[Optional[str]] = mapped_column(types.String())

    # Lifecycle timestamps
    created_at: Mapped[datetime.datetime] = mapped_column(
        types.DateTime(), nullable=False, default=datetime.datetime.utcnow
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        types.DateTime(),
        nullable=False,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )
