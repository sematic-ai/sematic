# Standard library
import datetime
import enum
import typing

# Third party
from sqlalchemy import Column, types, ForeignKey
from sqlalchemy.orm import validates

# Glow
from glow.db.models.base import Base


class RunArtifactRelationship(enum.Enum):
    INPUT = "INPUT"
    OUTPUT = "OUTPUT"

    @classmethod
    def values(cls) -> typing.Tuple[str, ...]:
        return tuple([value.value for value in cls.__members__.values()])


class RunArtifact(Base):

    __tablename__ = "run_artifacts"

    run_id: str = Column(types.String(), nullable=False, primary_key=True)
    artifact_id: str = Column(
        types.String(), ForeignKey("artifacts.id"), nullable=False, primary_key=True
    )
    name: str = Column(
        types.String(), ForeignKey("runs.id"), nullable=True, primary_key=True
    )
    relationship: str = Column(types.String(), nullable=False)
    created_at: datetime.datetime = Column(
        types.DateTime(), nullable=False, default=datetime.datetime.utcnow
    )
    updated_at: datetime.datetime = Column(
        types.DateTime(),
        nullable=False,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )

    @validates("relationship")
    def validate_relationship(selk, key, value) -> str:
        if value not in RunArtifactRelationship.values():
            raise ValueError(
                "Invalid run-artifact relationship: {}".format(repr(value))
            )

        return value
