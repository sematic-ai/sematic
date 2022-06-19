# Standard library
import datetime
import uuid

# Third party
from sqlalchemy import Column, types

# Sematic
from sematic.db.models.base import Base
from sematic.db.models.json_encodable_mixin import JSONEncodableMixin


class Note(Base, JSONEncodableMixin):

    __tablename__ = "notes"

    id: str = Column(types.String(), primary_key=True, default=lambda: uuid.uuid4().hex)
    author_id: str = Column(types.String(), nullable=False)
    note: str = Column(types.String(), nullable=False)
    run_id: str = Column(types.String(), nullable=False)
    root_id: str = Column(types.String(), nullable=False)
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
