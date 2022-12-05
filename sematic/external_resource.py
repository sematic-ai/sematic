from dataclasses import dataclass
from enum import Enum, unique

from sematic.calculator import Calculator

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
class ExternalResource:
    id: str
    status: ResourceStatus

    def activate(self):
        pass

    def deactivate(self):
        pass

    def check_status(self) -> ResourceStatus:
        pass

    def __enter__(self) -> "ExternalResource":
        pass

    def __exit__(self):
        pass
