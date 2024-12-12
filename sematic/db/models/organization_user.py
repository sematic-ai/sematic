# Standard Library
import datetime

# Third-party
from sqlalchemy import ForeignKey, types
from sqlalchemy.orm import Mapped, mapped_column  # type: ignore

# Sematic
from sematic.db.models.base import Base
from sematic.db.models.mixins.json_encodable_mixin import JSONEncodableMixin


class OrganizationUser(Base, JSONEncodableMixin):
    """
    Denotes that a User is a member of an Organization.

    Attributes
    ----------
    organization_id: str
        The ID of the Organization.
    user_id: str
        The ID of the User.
    admin: bool
        Whether the User is an "Administrator" for the Organization. Defaults to False.
    created_at: datetime.datetime
        The creation time. Defaults to the current time.
    updated_at: datetime.datetime
        The last update time. Auto-updates to the current time.
    """

    __tablename__ = "organizations_users"

    organization_id: Mapped[str] = mapped_column(
        types.String(), ForeignKey("organizations.id"), primary_key=True
    )
    user_id: Mapped[str] = mapped_column(
        types.String(), ForeignKey("users.id"), primary_key=True
    )
    admin: Mapped[bool] = mapped_column(types.Boolean, nullable=False, default=False)

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
