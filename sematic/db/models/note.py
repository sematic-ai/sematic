# Standard Library
import datetime
import uuid

# Third-party
from sqlalchemy import Column, ForeignKey, types

# Sematic
from sematic.db.models.base import Base
from sematic.db.models.mixins.has_user_mixin import HasUserMixin
from sematic.db.models.mixins.json_encodable_mixin import JSONEncodableMixin


class Note(HasUserMixin, Base, JSONEncodableMixin):

    __tablename__ = "notes"

    id: str = Column(types.String(), primary_key=True, default=lambda: uuid.uuid4().hex)
    note: str = Column(types.String(), nullable=False)
    run_id: str = Column(types.String(), ForeignKey("runs.id"), nullable=False)
    root_id: str = Column(types.String(), ForeignKey("runs.id"), nullable=False)
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
