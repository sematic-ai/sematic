# Standard Library
import datetime
import uuid

# Third-party
from sqlalchemy import ForeignKey, types
from sqlalchemy.orm import Mapped, mapped_column  # type: ignore

# Sematic
from sematic.db.models.base import Base
from sematic.db.models.mixins.has_user_mixin import HasUserMixin
from sematic.db.models.mixins.json_encodable_mixin import JSONEncodableMixin


class Note(HasUserMixin, Base, JSONEncodableMixin):
    __tablename__ = "notes"

    id: Mapped[str] = mapped_column(
        types.String(), primary_key=True, default=lambda: uuid.uuid4().hex
    )
    note: Mapped[str] = mapped_column(types.String(), nullable=False)
    run_id: Mapped[str] = mapped_column(
        types.String(), ForeignKey("runs.id"), nullable=False
    )
    root_id: Mapped[str] = mapped_column(
        types.String(), ForeignKey("runs.id"), nullable=False
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
