# Standard library
import datetime
from typing import Optional
import uuid

# Third-party
from sqlalchemy import Column, ForeignKey, types

# Glow
from glow.db.models.base import Base
from glow.db.models.json_encodable_mixin import JSONEncodableMixin


class Edge(Base, JSONEncodableMixin):

    __tablename__ = "edges"

    id: str = Column(types.String(), primary_key=True, default=lambda: uuid.uuid4().hex)

    # Edge endpoints
    source_run_id: Optional[str] = Column(
        types.String(), ForeignKey("artifacts.id"), nullable=True
    )
    source_name: Optional[str] = Column(types.String(), nullable=True)
    destination_run_id: Optional[str] = Column(
        types.String(), ForeignKey("artifacts.id"), nullable=True
    )
    destination_name: Optional[str] = Column(types.String(), nullable=True)

    # Artifact
    artifact_id: Optional[str] = Column(
        types.String(), ForeignKey("artifacts.id"), nullable=False
    )

    parent_id: Optional[str] = Column(types.String(), nullable=True)

    # Lifecycle timestamps
    created_at: datetime.datetime = Column(
        types.DateTime(), nullable=False, default=datetime.datetime.utcnow
    )
    updated_at: datetime.datetime = Column(
        types.DateTime(),
        nullable=False,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )

    _EQUALITY_FIELDS = (
        "source_run_id",
        "source_name",
        "destination_run_id",
        "destination_name",
        "artifact_id",
        "parent_id",
    )

    def __eq__(self, other) -> bool:
        return all(
            getattr(self, field) == getattr(other, field)
            for field in self._EQUALITY_FIELDS
        )

    def __hash__(self) -> int:
        return hash(
            ":".join(
                map(str, [getattr(self, field) for field in self._EQUALITY_FIELDS])
            )
        )

    def __repr__(self):
        return "Edge({})".format(
            ", ".join(
                "{}={}".format(column.name, repr(getattr(self, column.name)))
                for column in Edge.__table__.columns
            )
        )
