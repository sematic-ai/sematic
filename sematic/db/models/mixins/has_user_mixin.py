# Third-party
from sqlalchemy import Column, types
from sqlalchemy.orm import declarative_mixin


@declarative_mixin
class HasUserMixin:
    user_id: str = Column(types.String(), nullable=True)
