# Standard Library
import datetime
import uuid
from typing import Optional

# Third-party
from sqlalchemy import ForeignKey, types
from sqlalchemy.orm import Mapped, mapped_column  # type: ignore

# Sematic
from sematic.db.models.base import Base
from sematic.db.models.mixins.json_encodable_mixin import JSONEncodableMixin


class Edge(Base, JSONEncodableMixin):
    __tablename__ = "edges"

    id: Mapped[str] = mapped_column(
        types.String(), primary_key=True, default=lambda: uuid.uuid4().hex
    )

    # Edge endpoints
    source_run_id: Mapped[Optional[str]] = mapped_column(
        types.String(), ForeignKey("runs.id"), nullable=True, index=True
    )
    source_name: Mapped[Optional[str]] = mapped_column(types.String(), nullable=True)
    destination_run_id: Mapped[Optional[str]] = mapped_column(
        types.String(), ForeignKey("runs.id"), nullable=True, index=True
    )
    destination_name: Mapped[Optional[str]] = mapped_column(types.String(), nullable=True)

    # Artifact
    artifact_id: Mapped[Optional[str]] = mapped_column(
        types.String(), ForeignKey("artifacts.id"), nullable=True
    )

    parent_id: Mapped[Optional[str]] = mapped_column(
        types.String(), ForeignKey("edges.id"), nullable=True
    )

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

    _EQUALITY_FIELDS = (
        "source_run_id",
        "source_name",
        "destination_run_id",
        "destination_name",
        "artifact_id",
        "parent_id",
    )

    # Necessary for testing purposes, see test_local_resolver.py
    def __eq__(self, other) -> bool:
        return all(
            getattr(self, field) == getattr(other, field)
            for field in self._EQUALITY_FIELDS
        )

    def __hash__(self) -> int:
        return hash(
            ":".join(map(str, [getattr(self, field) for field in self._EQUALITY_FIELDS]))
        )

    def __repr__(self) -> str:
        fields = ", ".join(
            f"{field}={getattr(self, field)}"
            for field in (
                "id",
                "source_run_id",
                "destination_run_id",
                "destination_name",
                "artifact_id",
                "parent_id",
            )
        )
        return f"Edge({fields})"
