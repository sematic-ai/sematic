# Standard library
import datetime
import typing

# Third party
from sqlalchemy import Column, types

# Glow
from glow.abstract_future import FutureState
from glow.db.models.base import Base


class Run(Base):

    id: str = Column(types.String(), primary_key=True)
    future_state: FutureState = Column(types.Enum(FutureState), nullable=False)
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
