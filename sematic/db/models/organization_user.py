# Standard Library
import datetime

# Third-party
from sqlalchemy import Column, ForeignKey, types

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

    organization_id: str = Column(
        types.String(), ForeignKey("organizations.id"), primary_key=True
    )
    user_id: str = Column(types.String(), ForeignKey("users.id"), primary_key=True)
    admin: bool = Column(types.Boolean, nullable=False, default=False)

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
