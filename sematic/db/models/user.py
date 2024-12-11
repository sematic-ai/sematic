# Standard Library
import datetime
import uuid
from typing import Optional

# Third-party
from sqlalchemy import types
from sqlalchemy.orm import Mapped, mapped_column  # type: ignore

# Sematic
from sematic.db.models.base import Base
from sematic.db.models.mixins.json_encodable_mixin import (
    REDACTED_KEY,
    JSONEncodableMixin,
)


class User(Base, JSONEncodableMixin):
    """
    SQLAlchemy model for users
    """

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        types.String(), primary_key=True, default=lambda: uuid.uuid4().hex
    )
    email: Mapped[str] = mapped_column(
        types.String(), nullable=False, info={REDACTED_KEY: True}
    )
    first_name: Mapped[Optional[str]] = mapped_column(types.String(), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(types.String(), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(types.String(), nullable=True)
    api_key: Mapped[str] = mapped_column(
        types.String(), nullable=False, info={REDACTED_KEY: True}
    )

    created_at: Mapped[datetime.datetime] = mapped_column(
        types.DateTime(), nullable=False, default=datetime.datetime.utcnow
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        types.DateTime(),
        nullable=False,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )

    def get_friendly_name(self) -> str:
        """
        Returns a name that can be used to address the User, based on the filled values.
        """
        if self.first_name is not None and self.last_name is not None:
            return f"{self.first_name} {self.last_name}"
        if self.first_name is not None:
            return self.first_name
        if self.last_name is not None:
            return self.last_name
        return self.email
