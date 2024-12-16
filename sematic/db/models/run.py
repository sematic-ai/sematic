# Standard Library
import datetime
import importlib
import json
import re
from dataclasses import asdict
from typing import Dict, List, Optional, Union

# Third-party
from sqlalchemy import ForeignKey, types
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates  # type: ignore

# Sematic
from sematic.abstract_function import AbstractFunction
from sematic.abstract_future import FutureState
from sematic.db.models.base import Base
from sematic.db.models.mixins.has_organization_mixin import HasOrganizationMixin
from sematic.db.models.mixins.has_user_mixin import HasUserMixin
from sematic.db.models.mixins.json_encodable_mixin import (
    CONTAIN_FILTER_KEY,
    ENUM_KEY,
    JSON_KEY,
    JSONEncodableMixin,
    json_string_list_contains,
)
from sematic.db.models.resolution import Resolution
from sematic.resolvers.resource_requirements import ResourceRequirements
from sematic.types.serialization import (
    value_from_json_encodable,
    value_to_json_encodable,
)
from sematic.utils.exceptions import ExceptionMetadata


class Run(HasUserMixin, HasOrganizationMixin, Base, JSONEncodableMixin):
    """
    SQLAlchemy model for runs.

    Runs represent the execution of a :class:`sematic.Function`. They are
    created upon scheduling of a :class:`sematic.Future`.

    The relationship fields can also be used to filter runs. For example,
    to get all runs that have the resolution with kind "LOCAL", you can use
    filter like this:

    {"pipeline_run.kind": {"operator": "LOCAL"}}

    Currently supported relationship fields are:

    - root_run.*
    - pipeline_run.*

    Refer _extract_predicate() from request_parameters.py for more details.


    Attributes
    ----------
    id : str
        The UUID4 of the run.
    original_run_id : Optional[str]
        The id of the original run this run was cloned from, if any.
    future_state : str
        The state of the corresponding :class:`sematic.Future`. See
        :class:`sematic.abstract_future.FutureState` for possible values.
    name : str
        The name of the run. Defaults to the name of the :class:`sematic.Function`.
    function_path : str
        The full import path of the :class:`sematic.Function`.
    parent_id : Optional[str]
        The id of the parent run. A parent run is the run corresponding to
        the :class:`sematic.Function` encapsulating the current
        :class:`sematic.Function`.
    root_id : str
        ID of the root run of the current graph. The root run corresponds to the
        entry point of the graph, i.e. the one corresponding to the future on which
        `resolve` was called.
    description : Optional[str]
        The run's description. Defaults to the function's docstring.
    source_code : str
        The function's source code.
    nested_future_id : Optional[str]
        If the run resulted in returning a new future, this contains the id of that
        future.
    exception_metadata : Optional[ExceptionMetadata]
        The metadata for the exception from the function's execution, if any.
    external_exception_metadata : Optional[ExceptionMetadata]
        The metadata for the exception from the external compute infrastructure, if any.
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
        This is different from `ended_at` if the :class:`sematic.Function`
        returns a :class:`sematic.Future`.
    failed_at : Optional[datetime]
        Time at which the run has failed.
    resource_requirements_json : Optional[Dict[str, Any]]
        The compute resources requested for the execution.
    cache_key : Optional[str]
        If present, the key under which the run's output artifact will be cached.
    user_id: Optional[str]
        Users who submitted this run.
    organization_id: Optional[str]
        The organization under which this resolution was submitted.
    """

    __tablename__ = "runs"

    id: Mapped[str] = mapped_column(types.String(), primary_key=True)
    original_run_id: Mapped[Optional[str]] = mapped_column(types.String(), nullable=True)
    future_state: Mapped[FutureState] = mapped_column(  # type: ignore
        types.String(), nullable=False, info={ENUM_KEY: FutureState}
    )
    name: Mapped[str] = mapped_column(types.String(), nullable=True)
    function_path: Mapped[str] = mapped_column(types.String(), nullable=False, index=True)
    parent_id: Mapped[Optional[str]] = mapped_column(types.String(), nullable=True)
    root_id: Mapped[str] = mapped_column(
        types.String(), ForeignKey("runs.id"), nullable=False
    )
    description: Mapped[Optional[str]] = mapped_column(types.String(), nullable=True)
    tags: Mapped[List[str]] = mapped_column(  # type: ignore
        types.String(),
        nullable=False,
        default="[]",
        info={JSON_KEY: True, CONTAIN_FILTER_KEY: json_string_list_contains},
    )
    source_code: Mapped[str] = mapped_column(types.String(), nullable=False)

    nested_future_id: Mapped[Optional[str]] = mapped_column(types.String(), nullable=True)
    exception_metadata_json: Mapped[Optional[Dict[str, Union[str, List[str]]]]] = (
        mapped_column(types.JSON(), nullable=True)
    )
    external_exception_metadata_json: Mapped[
        Optional[Dict[str, Union[str, List[str]]]]
    ] = mapped_column(types.JSON(), nullable=True)

    container_image_uri: Mapped[Optional[str]] = mapped_column(
        types.String(), nullable=True
    )

    # Lifecycle timestamps
    created_at: Mapped[datetime.datetime] = mapped_column(
        types.DateTime(), nullable=False, default=datetime.datetime.utcnow
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        types.DateTime(),
        nullable=False,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )
    started_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        types.DateTime(), nullable=True
    )
    ended_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        types.DateTime(), nullable=True
    )
    resolved_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        types.DateTime(), nullable=True
    )
    failed_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        types.DateTime(), nullable=True
    )
    resource_requirements_json: Mapped[Optional[str]] = mapped_column(
        types.JSON(), nullable=True, info={JSON_KEY: True}
    )
    cache_key: Mapped[Optional[str]] = mapped_column(
        types.String(), nullable=True, index=True
    )

    # Relationships
    root_run: Mapped["Run"] = relationship(  # type: ignore
        "Run",
        remote_side=[id],
        lazy="select",
    )
    pipeline_run: Mapped[Resolution] = relationship(  # type: ignore
        "Resolution",
        foreign_keys=[root_id],
        viewonly=True,
        primaryjoin="Resolution.root_id == Run.root_id",
        lazy="select",
    )

    @validates("future_state")
    def validate_future_state(self, _, value) -> str:
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
    def convert_tags_to_json(self, _, value) -> str:
        if isinstance(value, list):
            return json.dumps(value)

        return value

    @validates("description")
    def strip_description(self, _, value) -> str:
        if value is not None:
            value = re.sub(r"\n( {4}|\t)", "\n", value.strip())

        return value

    @property
    def exception_metadata(self) -> Optional[ExceptionMetadata]:
        return Run._dict_to_exception_metadata(self.exception_metadata_json)

    @exception_metadata.setter
    def exception_metadata(self, exception_metadata: Optional[ExceptionMetadata]) -> None:
        self.exception_metadata_json = Run._exception_metadata_to_dict(exception_metadata)

    @property
    def external_exception_metadata(self) -> Optional[ExceptionMetadata]:
        return Run._dict_to_exception_metadata(self.external_exception_metadata_json)

    @external_exception_metadata.setter
    def external_exception_metadata(
        self, exception_metadata: Optional[ExceptionMetadata]
    ) -> None:
        self.external_exception_metadata_json = Run._exception_metadata_to_dict(
            exception_metadata
        )

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

    def get_func(self) -> AbstractFunction:
        split_function_path = self.function_path.split(".")
        import_path, func_name = (
            ".".join(split_function_path[:-1]),
            split_function_path[-1],
        )
        try:
            func = getattr(importlib.import_module(import_path), func_name)
        except (ImportError, AttributeError) as e:
            raise type(e)(
                f"Unable to find this run's function at {import_path}.{func_name}, "
                f"did it change location? {e}"
            )

        return func

    def __repr__(self):
        return ", ".join(
            (
                f"Run(id={self.id}",
                f"function_path={self.function_path}",
                f"future_state={self.future_state}",
                f"parent_id={self.parent_id}",
                f"root_id={self.root_id}",
                f"created_at={self.created_at}",
                f"resolved_at={self.resolved_at}",
                f"failed_at={self.failed_at})",
            )
        )

    @staticmethod
    def _exception_metadata_to_dict(
        exception_metadata: Optional[ExceptionMetadata],
    ) -> Optional[Dict[str, Union[str, List[str]]]]:
        """
        Converts an `ExceptionMetadata` object to its Dict representation.
        """
        return asdict(exception_metadata) if exception_metadata is not None else None

    @staticmethod
    def _dict_to_exception_metadata(
        dict_: Optional[Dict[str, Union[str, List[str]]]],
    ) -> Optional[ExceptionMetadata]:
        """
        Instantiates an `ExceptionMetadata` object from a Dict representation.
        """
        if dict_ is None:
            return None

        return ExceptionMetadata(
            repr=dict_["repr"],  # type: ignore
            name=dict_["name"],  # type: ignore
            module=dict_["module"],  # type: ignore
            ancestors=dict_.get("ancestors", []),  # type: ignore
        )

    @property
    def tag_list(self) -> List[str]:
        # See https://github.com/sematic-ai/sematic/issues/838
        if isinstance(self.tags, str):
            return json.loads(self.tags)
        return self.tags
