# Standard Library
from typing import Any, Dict, Tuple, Type, Union

# Third-party
from sqlalchemy import Column, types
from sqlalchemy.orm import validates

# Sematic
from sematic.db.models.base import Base
from sematic.db.models.json_encodable_mixin import JSONEncodableMixin
from sematic.external_resource import ExternalResource, ResourceState
from sematic.types.serialization import (
    type_from_json_encodable,
    type_to_json_encodable,
    value_from_json_encodable,
    value_to_json_encodable,
)
from sematic.utils.exceptions import MissingPluginError

TypeSerialization = Dict[str, Any]


class ExternalResourceRecord(Base, JSONEncodableMixin):
    """A DB record for an ExternalResource and its history.

    Attributes
    ----------
    id:
        The unique id of the external resource
    resource_state:
        The current state of the resource
    locally_allocated:
        Whether or not the resource was locally allocated
    status_message:
        The most recent status message for the resource
    last_updated_epoch_seconds:
        The time that the resource was last updated, expressed as epoch seconds
    type_serialization:
        The Sematic serialization of the type. This may be different from the
        serialization for ExternalResource itself, since the resource will be a
        subclass of ExternalResource.
    value_serialization:
        The Sematic serialization of the object. This will contain extra fields
        unique to the subclasses of ExternalResource. It also does contain
        json variants of some of the status fields above, but the duplicated values
        should match.
    history_serializations:
        The Sematic serialization of the objects. Any time the ExternalResource object
        changes in such a way as to make the instances compare as not equal, a new
        entry will be added to this list. Element 0 is the most recent, element N
        the oldest.
    """

    # Q: Why duplicate data that's already in the json of value_serialization as columns?
    # A: For two reasons:
    #    1. It gives us freedom to refactor the dataclass for ExternalResource later
    #    to move fields around, while allowing the database columns to stay stable.
    #    2. It allows for more efficient queries on the explicit columns rather than
    #    requiring json traversal.

    __tablename__ = "external_resources"

    id: str = Column(types.String(), primary_key=True)
    resource_state: ResourceState = Column(  # type: ignore
        types.Enum(ResourceState),
        nullable=False,
    )
    locally_allocated: bool = Column(  # type: ignore
        types.BOOLEAN,
        nullable=False,
    )
    status_message: str = Column(types.String(), nullable=False)
    last_updated_epoch_seconds: int = Column(types.BIGINT(), nullable=False)
    type_serialization: TypeSerialization = Column(types.JSON(), nullable=False)
    value_serialization: Dict[str, Any] = Column(types.JSON(), nullable=False)
    history_serializations: Tuple[Dict[str, Any], ...] = Column(  # type: ignore
        types.JSON(), nullable=False
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

    @classmethod
    def from_resource(
        cls, resource: ExternalResource, locally_allocated: bool
    ) -> "ExternalResourceRecord":
        if not isinstance(resource, ExternalResource):
            raise ValueError(
                f"resource must be an instance of a subclass of "
                f"ExternalResource. Was: {resource} of type "
                f"'{type(resource)}'"
            )
        type_serialization = type_to_json_encodable(type(resource))
        value_serialization = value_to_json_encodable(resource, type(resource))
        return ExternalResourceRecord(
            id=resource.id,
            resource_state=resource.status.state,
            locally_allocated=locally_allocated,
            status_message=resource.status.message,
            last_updated_epoch_seconds=resource.status.last_update_epoch_time,
            type_serialization=type_serialization,
            value_serialization=value_serialization,
            history_serializations=(value_serialization,),
        )

    def get_resource_type(self) -> Type[ExternalResource]:
        try:
            return type_from_json_encodable(self.type_serialization)
        except Exception:
            type_name = self.type_serialization["type"][1]
            import_path = self.type_serialization["type"][2]["import_path"]
            raise MissingPluginError(f"{import_path}.{type_name}")

    def set_resource_type(self, type_: Type[ExternalResource]) -> None:
        if not issubclass(type_, ExternalResource):
            raise ValueError(
                f"type_ must be a subclass of ExternalResource. Was: {type_}"
            )
        self.type_serialization = type_to_json_encodable(type_)

    resource_type = property(get_resource_type, set_resource_type)

    def get_resource(self) -> ExternalResource:
        return value_from_json_encodable(self.value_serialization, self.resource_type)

    def set_resource(self, resource: ExternalResource) -> None:
        if not isinstance(resource, ExternalResource):
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
        self.last_updated_epoch_seconds = resource.status.last_update_epoch_time

        self.value_serialization = serialization

    resource = property(get_resource, set_resource)

    @property
    def history(self) -> Tuple[ExternalResource, ...]:
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
        return f"ExternalResourceRecord({fields}, ...)"
