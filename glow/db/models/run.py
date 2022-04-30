# Standard library
import datetime
import typing

# Third party
from sqlalchemy import Column, types
from sqlalchemy.orm import validates

# Glow
from glow.abstract_future import FutureState
from glow.db.models.base import Base


class Run(Base):

    id: str = Column(types.String(), primary_key=True)
    future_state: FutureState = Column(types.String(), nullable=False)
    name: str = Column(types.String(), nullable=True)
    calculator_path: str = Column(types.String(), nullable=False)
    parent_id: str = Column(types.String(), nullable=True)

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
    started_at: typing.Optional[datetime.datetime] = Column(
        types.DateTime(), nullable=True
    )
    ended_at: typing.Optional[datetime.datetime] = Column(
        types.DateTime(), nullable=True
    )
    resolved_at: typing.Optional[datetime.datetime] = Column(
        types.DateTime(), nullable=True
    )
    failed_at: typing.Optional[datetime.datetime] = Column(
        types.DateTime(), nullable=True
    )

    @validates("future_state")
    def validate_future_state(self, key, value):
        if value not in FutureState.__members__.values():
            raise ValueError(
                (
                    "The value of `Run.future_state`"
                    " must be one of the values in `FutureState`."
                )
            )
        return value
