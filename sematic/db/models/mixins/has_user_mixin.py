# Standard Library
from typing import Optional

# Third-party
from sqlalchemy import Column, ForeignKey, types
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Mapped, declarative_mixin


@declarative_mixin
class HasUserMixin:
    @declared_attr
    def user_id(cls) -> Mapped[Optional[str]]:
        return Column(types.String(), ForeignKey("users.id"), nullable=True)
