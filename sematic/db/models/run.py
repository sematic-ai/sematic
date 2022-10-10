# Standard Library
import datetime
import json
import re
from dataclasses import asdict
from typing import Any, Dict, List, Optional, Sequence, Tuple

# Third party
from sqlalchemy import Column, types
from sqlalchemy.orm import validates

# Sematic
from sematic.abstract_future import FutureState
from sematic.db.models.base import Base
from sematic.db.models.has_external_jobs_mixin import HasExternalJobsMixin
from sematic.db.models.json_encodable_mixin import (
    ENUM_KEY,
    JSON_KEY,
    JSONEncodableMixin,
)
from sematic.resolvers.resource_requirements import ResourceRequirements
from sematic.scheduling.external_job import ExternalJob
from sematic.types.serialization import (
    value_from_json_encodable,
    value_to_json_encodable,
)
from sematic.utils.exceptions import ExceptionMetadata


class Run(Base, JSONEncodableMixin, HasExternalJobsMixin):
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
        The exception from the calculator's execution
    nested_future_id:
        If the run resulted in returning a new future, this contains the id of that
        future
    external_jobs_json:
        A list of external compute jobs associated with the execution of this run.
        There may be multiple due to run retries. The field is a json string, but
        the dataclass version of the jobs can be accessed with the external_jobs
        property.
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
    resource_requirements_json : Optional[Dict[str, Any]]
        The compute resources requested for the execution.
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
    nested_future_id: str = Column(types.String(), nullable=True)
    external_jobs_json: Optional[List[Dict[str, Any]]] = Column(
        types.JSON(), nullable=True
    )
    exception_json: Optional[Dict[str, str]] = Column(types.JSON(), nullable=True)

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
    resource_requirements_json: Optional[str] = Column(
        types.JSON(), nullable=True, info={JSON_KEY: True}
    )

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

    @property
    def exception(self) -> Optional[ExceptionMetadata]:
        if self.exception_json is None:
            return None

        return ExceptionMetadata(
            repr=self.exception_json["repr"],
            name=self.exception_json["name"],
            module=self.exception_json["module"],
        )

    @exception.setter
    def exception(self, exception_metadata: Optional[ExceptionMetadata]):
        if exception_metadata is None:
            self.exception_json = None
        else:
            self.exception_json = asdict(exception_metadata)

    @property
    def external_jobs(self) -> Tuple[ExternalJob, ...]:
        """Representations of the external compute jobs used for the run."""
        encodables = self.external_jobs_json
        encodables = encodables if encodables is not None else []
        return tuple(value_from_json_encodable(job, ExternalJob) for job in encodables)

    @external_jobs.setter
    def external_jobs(self, jobs: Sequence[ExternalJob]):
        self.external_jobs_json = [
            value_to_json_encodable(job, ExternalJob) for job in jobs
        ]

    @property
    def resource_requirements(self) -> Optional[ResourceRequirements]:
        if self.resource_requirements_json is None:
            return None

        json_encodable = json.loads(self.resource_requirements_json)
        return value_from_json_encodable(json_encodable, ResourceRequirements)

    @resource_requirements.setter
    def resource_requirements(self, value: Optional[ResourceRequirements]) -> None:
        if value is None:
            self.resource_requirements_json = None
            return
        self.resource_requirements_json = json.dumps(
            value_to_json_encodable(value, ResourceRequirements)
        )
