# Standard Library
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum, unique

# Sematic
from sematic.future_context import AbstractExternalResource


@unique
class ResourceStatusState(Enum):
    CREATED = "CREATED"
    ACTIVATING = "ACTIVATING"
    ACTIVE = "ACTIVE"
    DEACTIVATING = "DEACTIVATING"
    INACTIVE = "INACTIVE"


@dataclass(frozen=True)
class ResourceStatus:
    state: ResourceStatusState
    message: str
    last_update_epoch_time: int


@dataclass(frozen=True)
class ExternalResource(AbstractExternalResource):
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    status: ResourceStatus = field(
        default_factory=lambda: ResourceStatus(
            state=ResourceStatusState.CREATED,
            message="Resource has not been activated yet",
            last_update_epoch_time=int(time.time()),
        )
    )

    def __post_init__(self):
        try:
            uuid.UUID(hex=self.id)
        except ValueError:
            raise ValueError(f"ExternalResource had an invalid uuid: '{self.id}'")
        if not isinstance(self.status, ResourceStatus):
            raise ValueError(f"ExternalResource had invalid status: '{self.status}'")

    def activate(self, is_local: bool) -> "ExternalResource":
        raise NotImplementedError(
            "Subclasses of ExternalResource should implement .activate(is_local)"
        )

    def deactivate(self) -> "ExternalResource":
        pass

    def update(self) -> "ExternalResource":
        raise NotImplementedError(
            "Subclasses of ExternalResource should implement .update()"
        )
