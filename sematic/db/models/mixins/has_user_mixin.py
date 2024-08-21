# Third-party
from sqlalchemy import ForeignKey, types
from sqlalchemy.orm import Mapped, mapped_column, declared_attr


class HasUserMixin:
    @declared_attr
    def user_id(cls) -> Mapped[types.String]:
        return mapped_column(types.String(), ForeignKey("users.id"), nullable=True)
