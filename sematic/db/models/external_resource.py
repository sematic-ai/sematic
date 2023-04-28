# Standard Library
import datetime
from copy import deepcopy
from typing import Any, Dict, Tuple, Type, Union

# Third-party
from sqlalchemy import Column, types
from sqlalchemy.orm import validates

# Sematic
from sematic.db.models.base import Base
from sematic.db.models.mixins.json_encodable_mixin import JSONEncodableMixin
from sematic.plugins.abstract_external_resource import (
    AbstractExternalResource,
    ManagedBy,
    ResourceState,
    ResourceStatus,
)
from sematic.types.serialization import (
    type_from_json_encodable,
    type_to_json_encodable,
    value_from_json_encodable,
    value_to_json_encodable,
)
from sematic.utils.exceptions import MissingPluginError

TypeSerialization = Dict[str, Any]


class ExternalResource(Base, JSONEncodableMixin):
    """A DB record for an AbstractExternalResource (dataclass) and its history.

    Attributes
    ----------
    id:
        The unique id of the external resource
    resource_state:
        The current state of the resource
    managed_by:
        Whether the resource is managed locally, remotely, or its management
        state is not known.
    status_message:
        The most recent status message for the resource
    last_updated_epoch_seconds:
        The time that the resource was last updated against the resource objects
        it represnets, expressed as epoch seconds. Ex: the last time Spark was
        queried for whether the cluster was alive. This differs from updated_at
        in that it relates to the updates against the external resources, while
        updated_at relates to updates of the DB record. It is in epoch seconds
        rather than as a datetime object because it will primarily be used in
        arithmetic operations with time (ex: comparing which value is more recent,
        amount of elapsed time since last update) rather than for human-readability
        of absolute time.
    type_serialization:
        The Sematic serialization of the type. This may be different from the
        serialization for AbstractExternalResource itself, since the resource will
        be a subclass of AbstractExternalResource.
    value_serialization:
        The Sematic serialization of the object. This will contain extra fields
        unique to the subclasses of AbstractExternalResource. It also does contain
        json variants of some of the status fields above, but the duplicated values
        should match.
    history_serializations:
        The Sematic serialization of the objects. Any time the AbstractExternalResource
        object changes in such a way as to make the instances compare as not equal, a
        new entry will be added to this list. Element 0 is the most recent, element N
        the oldest.
    created_at:
        The time this record was created in the DB.
    updated_at:
        The time this record was last updated in the DB. See documentation in
        last_updated_epoch_seconds for how this relates to that field.
    """

    # Q: Why duplicate data that's already in the json of value_serialization as columns?
    # A: For two reasons:
    #    1. It gives us freedom to refactor the dataclass for AbstractExternalResource
    #    later to move fields around, while allowing the database columns to stay
    #    stable.
    #    2. It allows for more efficient queries on the explicit columns rather than
    #    requiring json traversal.

    __tablename__ = "external_resources"

    id: str = Column(types.String(), primary_key=True)
    resource_state: ResourceState = Column(  # type: ignore
        types.Enum(ResourceState),
        nullable=False,
    )
    managed_by: ManagedBy = Column(  # type: ignore
        types.Enum(ManagedBy),
        nullable=False,
    )
    status_message: str = Column(types.String(), nullable=False)
    last_updated_epoch_seconds: int = Column(types.BIGINT(), nullable=False)
    type_serialization: TypeSerialization = Column(types.JSON(), nullable=False)
    value_serialization: Dict[str, Any] = Column(types.JSON(), nullable=False)
    history_serializations: Tuple[Dict[str, Any], ...] = Column(  # type: ignore
        types.JSON(), nullable=False
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

    @validates("resource_state")
    def validate_resource_state(
        self, key: Any, resource_state: Union[str, ResourceState]
    ) -> ResourceState:
        if isinstance(resource_state, str):
            return ResourceState[resource_state]
        elif isinstance(resource_state, ResourceState):
            return resource_state
        raise ValueError(f"Cannot make a ResourceState from {resource_state}")

    @validates("managed_by")
    def validate_managed_by(
        self, key: Any, managed_by: Union[str, ManagedBy]
    ) -> ManagedBy:
        if isinstance(managed_by, str):
            return ManagedBy[managed_by]
        elif isinstance(managed_by, ManagedBy):
            return managed_by
        raise ValueError(f"Cannot make a ManagedBy from {managed_by}")

    @classmethod
    def from_resource(cls, resource: AbstractExternalResource) -> "ExternalResource":
        if not isinstance(resource, AbstractExternalResource):
            raise ValueError(
                f"resource must be an instance of a subclass of "
                f"ExternalResource. Was: {resource} of type "
                f"'{type(resource)}'"
            )
        type_serialization = type_to_json_encodable(type(resource))
        value_serialization = value_to_json_encodable(resource, type(resource))
        return ExternalResource(
            id=resource.id,
            resource_state=resource.status.state,
            managed_by=resource.status.managed_by,
            status_message=resource.status.message,
            last_updated_epoch_seconds=resource.status.last_update_epoch_time,
            type_serialization=type_serialization,
            value_serialization=value_serialization,
            history_serializations=(value_serialization,),
        )

    def get_resource_type(self) -> Type[AbstractExternalResource]:
        try:
            return type_from_json_encodable(self.type_serialization)
        except ImportError:
            type_name = self.type_serialization["type"][1]
            import_path = self.type_serialization["type"][2]["import_path"]

            # We are unable to load the type for the external resource.
            # This means the type must not be present, which is tantamount
            # to a missing plugin for that external resource type.
            raise MissingPluginError(f"{import_path}.{type_name}")

    def set_resource_type(self, type_: Type[AbstractExternalResource]) -> None:
        if not issubclass(type_, AbstractExternalResource):
            raise ValueError(
                f"type_ must be a subclass of ExternalResource. Was: {type_}"
            )
        self.type_serialization = type_to_json_encodable(type_)

    resource_type = property(get_resource_type, set_resource_type)

    def get_resource(self) -> AbstractExternalResource:
        return value_from_json_encodable(self.value_serialization, self.resource_type)

    def set_resource(self, resource: AbstractExternalResource) -> None:
        if not isinstance(resource, AbstractExternalResource):
            raise ValueError(
                f"resource must be a subclass of ExternalResource. Was: {type(resource)}"
            )
        current_resource = self.resource
        current_resource.validate_transition(resource)

        serialization = value_to_json_encodable(resource, type(resource))
        if resource != current_resource:
            history = list(self.history_serializations)
            history.insert(0, serialization)
            self.history_serializations = tuple(history)

        self.resource_state = resource.status.state
        self.status_message = resource.status.message
        self.managed_by = resource.status.managed_by
        self.last_updated_epoch_seconds = resource.status.last_update_epoch_time

        self.value_serialization = serialization

    resource = property(get_resource, set_resource)

    def force_to_terminal_state(self, reason: str):
        """Force this record to be in a terminal state.

        This method is safe against errors loading the resource
        class. It will update the resource history properly.

        Parameters
        ----------
        reason:
            A human-readable explanation for why the resource is being
            forced into a terminal state.
        """
        # We may not be able to deserialize the resource,
        # so we'll work directly with the serializations.
        new_value = deepcopy(self.value_serialization)
        state = ResourceState.FORCE_KILLED
        message = f"Forced to terminal state: {reason}"
        status = ResourceStatus(
            state=state,
            message=message,
            managed_by=self.managed_by,
        )
        status_serialization = value_to_json_encodable(
            status,
            ResourceStatus,
        )
        new_value["values"]["status"] = status_serialization
        self.value_serialization = new_value
        self.resource_state = state
        self.status_message = message
        self.last_updated_epoch_seconds = status.last_update_epoch_time
        history = list(self.history_serializations)
        history.insert(0, new_value)
        self.history_serializations = tuple(history)

    @property
    def history(self) -> Tuple[AbstractExternalResource, ...]:
        type_ = self.resource_type
        return tuple(
            value_from_json_encodable(r, type_) for r in self.history_serializations
        )

    def __repr__(self) -> str:
        key_value_strings = [
            f"{field}={getattr(self, field)}"
            for field in (
                "id",
                "resource_state",
                "status_message",
            )
        ]
        key_value_strings.append(f"resource_type={self.type_serialization['type'][1]}")

        fields = ", ".join(key_value_strings)
        return f"ExternalResource({fields}, ...)"
