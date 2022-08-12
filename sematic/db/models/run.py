# Standard Library
import datetime
import json
import re
from typing import List, Optional

# Third party
from sqlalchemy import Column, types
from sqlalchemy.orm import validates

# Sematic
from sematic.abstract_future import FutureState
from sematic.db.models.base import Base
from sematic.db.models.json_encodable_mixin import (
    ENUM_KEY,
    JSON_KEY,
    JSONEncodableMixin,
)


class Run(Base, JSONEncodableMixin):
    """
    SQLAlchemy model for runs.

    Runs represent the execution of a :class:`sematic.Calculator`. They are
    created upon scheduling of a :class:`sematic.Future`.

    Attributes
    ----------
    id : str
        The UUID4 of the run.
    future_state : str
        The state of the corresponding :class:`sematic.Future`. See
        :class:`sematic.abstract_future.FutureState` for possible values.
    name : str
        The name of the run. Defaults to the name of the :class:`sematic.Calculator`.
    calculator_path : str
        The full import path of the :class:`sematic.Calculator`.
    parent_id : Optional[str]
        The id of the parent run. A parent run is the run corresponding to
        the :class:`sematic.Calculator` encapsulating the current
        :class:`sematic.Calculator`.
    root_id : str
        ID of the root run of the current graph. The root run corresponds to the
        entry point of the graph, i.e. the one corresponding to the future on which
        `resolve` was called.
    description: Optional[str]
        The run's description. Defaults to the function's docstring.
    source_code: str
        The calculator's source code.
    exception: Optional[str]
        The calculator's source code.
    created_at : datetime
        Time of creating of the run record in the DB.
    updated_at : datetime
        Time of last update of the run record in the DB.
    started_at : Optional[datetime]
        Time at which the run has actually started executing.
    ended_at : Optional[datetime]
        Time at which the run has finished running.
    resolved_at : Optional[datetime]
        Time at which the run has a concrete resolved value.
        This is different from `ended_at` if the :class:`sematic.Calculator`
        returns a :class:`sematic.Future`.
    failed_at : Optional[datetime]
        Time at which the run has failed.

    """

    __tablename__ = "runs"

    id: str = Column(types.String(), primary_key=True)
    future_state: FutureState = Column(  # type: ignore
        types.String(), nullable=False, info={ENUM_KEY: FutureState}
    )
    name: str = Column(types.String(), nullable=True)
    calculator_path: str = Column(types.String(), nullable=False)
    parent_id: Optional[str] = Column(types.String(), nullable=True)
    root_id: str = Column(types.String(), nullable=False)
    description: Optional[str] = Column(types.String(), nullable=True)
    tags: List[str] = Column(  # type: ignore
        types.String(), nullable=False, default="[]", info={JSON_KEY: True}
    )
    source_code: str = Column(types.String(), nullable=False)
    exception: str = Column(types.String(), nullable=True)
    nested_future_id: str = Column(types.String(), nullable=True)

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
    started_at: Optional[datetime.datetime] = Column(types.DateTime(), nullable=True)
    ended_at: Optional[datetime.datetime] = Column(types.DateTime(), nullable=True)
    resolved_at: Optional[datetime.datetime] = Column(types.DateTime(), nullable=True)
    failed_at: Optional[datetime.datetime] = Column(types.DateTime(), nullable=True)

    @validates("future_state")
    def validate_future_state(self, key, value) -> str:
        """
        Validates that the future_state value is allowed.
        """
        if isinstance(value, FutureState):
            return value.value

        try:
            return FutureState[value].value
        except Exception:
            raise ValueError("future_state must be a FutureState, got {}".format(value))

    @validates("tags")
    def convert_tags_to_json(self, key, value) -> str:
        if isinstance(value, list):
            return json.dumps(value)

        return value

    @validates("description")
    def strip_description(self, key, value) -> str:
        if value is not None:
            value = re.sub(r"\n\s{4}", "\n", value.strip())

        return value
