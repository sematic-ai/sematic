# Standard Library
from typing import Optional

# Third-party
from sqlalchemy import Column, ForeignKey, types
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Mapped, declarative_mixin


@declarative_mixin
class HasOrganizationMixin:
    """
    Mixin for models that may have an associated Organization.

    Attributes
    ----------
    organization_id: Optional[str]
        The ID of the Organization, if any.
    """

    @declared_attr
    def organization_id(cls) -> Mapped[Optional[str]]:
        return Column(types.String(), ForeignKey("organizations.id"), nullable=True)
