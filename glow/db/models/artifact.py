# Standard library
import datetime

# Third party
from sqlalchemy import Column, types

# Glow
from glow.db.models.base import Base
from glow.db.models.json_encodable_mixin import JSONEncodableMixin


class Artifact(Base, JSONEncodableMixin):

    __tablename__ = "artifacts"

    id: str = Column(types.String(), primary_key=True)
    json_summary: str = Column(types.String(), nullable=False)
    created_at: datetime.datetime = Column(
        types.DateTime(), nullable=False, default=datetime.datetime.utcnow
    )
    updated_at: datetime.datetime = Column(
        types.DateTime(),
        nullable=False,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )
