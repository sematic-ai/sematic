# Standard library
import datetime

# Third party
from sqlalchemy import Column, types

# Sematic
from sematic.db.models.base import Base
from sematic.db.models.json_encodable_mixin import JSONEncodableMixin, JSON_KEY


class Artifact(Base, JSONEncodableMixin):

    __tablename__ = "artifacts"

    id: str = Column(types.String(), primary_key=True)
    json_summary: str = Column(types.JSON(), nullable=False, info={JSON_KEY: True})
    type_serialization: str = Column(
        types.JSON(), nullable=False, info={JSON_KEY: True}
    )
    created_at: datetime.datetime = Column(
        types.DateTime(), nullable=False, default=datetime.datetime.utcnow
    )
    updated_at: datetime.datetime = Column(
        types.DateTime(),
        nullable=False,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )
