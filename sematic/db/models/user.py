# Standard Library
import datetime
from typing import Optional

# Third-party
from sqlalchemy import Column, types

# Sematic
from sematic.db.models.base import Base
from sematic.db.models.json_encodable_mixin import REDACTED_KEY, JSONEncodableMixin


class User(Base, JSONEncodableMixin):
    """
    SQLAlchemy model for users
    """

    __tablename__ = "users"

    email: str = Column(types.String(), primary_key=True)
    first_name: Optional[str] = Column(types.String(), nullable=True)
    last_name: Optional[str] = Column(types.String(), nullable=True)
    avatar_url: Optional[str] = Column(types.String(), nullable=True)
    api_key: str = Column(types.String(), nullable=False, info={REDACTED_KEY: True})

    created_at: datetime.datetime = Column(
        types.DateTime(), nullable=False, default=datetime.datetime.utcnow
    )
    updated_at: datetime.datetime = Column(
        types.DateTime(),
        nullable=False,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )
