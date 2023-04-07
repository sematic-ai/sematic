# Standard Library
from typing import Optional

# Third-party
from sqlalchemy import Column, types
from sqlalchemy.orm import declarative_mixin


@declarative_mixin
class HasUserMixin:
    user_id: Optional[str] = Column(types.String(), nullable=True)
