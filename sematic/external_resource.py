# Standard Library
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum, unique
from typing import final

# Sematic
from sematic.future_context import AbstractExternalResource
from sematic.utils.exceptions import IllegalStateTransitionError


@unique
class ResourceState(Enum):
    """Represents the state of an external resource

    Attributes
    ----------
    CREATED:
        The object representing the resource has been instantiated in-memory
        but no logic to allocate the resource has been executed.
    ACTIVATING:
        The resource is being allocated. This may take time. The resource cannot
        be used yet.
    ACTIVE:
        The resource is allocated and ready for use.
    DEACTIVATING:
        The resource is being deactivated, and likely is no longer usable.
    INACTIVE:
        The resource has been deactivated and may not even exist anymore.
        It is not usable.
    """

    CREATED = "CREATED"
    ACTIVATING = "ACTIVATING"
    ACTIVE = "ACTIVE"
    DEACTIVATING = "DEACTIVATING"
    INACTIVE = "INACTIVE"

    def is_allowed_transition(self, other_state: "ResourceStatus") -> bool:
        """True if going from the current state to the other is allowed, otherwise False.

        Parameters
        ----------
        other_state:
            The state being transitioned to

        Returns
        -------
        True if going from the current state to the other is allowed, otherwise False.
        """
        return other_state in _ALLOWED_TRANSITIONS[self]

    def is_terminal(self) -> bool:
        """True if there are no states that can follow this one, False otherwise."""
        return len(_ALLOWED_TRANSITIONS[self]) == 0


_ALLOWED_TRANSITIONS = {
    None: {ResourceState.CREATED},
    ResourceState.CREATED: {
        # Created -> Activating: normal progression for activation
        ResourceState.ACTIVATING,
    },
    ResourceState.ACTIVATING: {
        # Activating -> Active: normal progression for successful activation
        ResourceState.ACTIVE,
        # Activating -> Deactivating: activation failed, immediate deactivation
        ResourceState.DEACTIVATING,
    },
    ResourceState.ACTIVE: {
        # Active -> Deactivating:
        #   - possibly normal termination, due to no longer being needed.
        #   - possibly an error with the resource. Status message should have more info.
        ResourceState.DEACTIVATING,
    },
    ResourceState.DEACTIVATING: {
        # Deactivating -> Inactive: normal progression for deactivation
        ResourceState.INACTIVE,
    },
    ResourceState.DEACTIVATING: {},
}


@dataclass(frozen=True)
class ResourceStatus:
    """The status of the resource

    Attributes
    ----------
    state:
        The discrete state that the resource is in
    message:
        A human-readable message about why the resource entered this state
    last_update_epoch_time:
        The last time this status was checked against the actual external resource
    """

    state: ResourceState
    message: str
    last_update_epoch_time: int


@dataclass(frozen=True)
class ExternalResource(AbstractExternalResource):
    """Represents a resource tracked by Sematic for usage in Sematic funcs.

    Examples of possible external resources include small data processing
    clusters or distributed training clusters.

    Specific external resources should inherit from this class. They may add their
    own dataclass attributes and must implement the _do_activate, _do_deactivate, and
    _do_update methods on this class.

    This class represents immutable objects. As with immutable strings, the
    preferred pattern is to replace instances with updated copies rather
    than modify in-place. This allows for better control over validation of
    objects and state transitions.

    Attributes
    ----------
    id:
        A UUID representing this particular resource instance
    status:
        Information about the current status of the resource
    """

    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    status: ResourceStatus = field(
        default_factory=lambda: ResourceStatus(
            state=ResourceState.CREATED,
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

    @final
    def activate(self, is_local: bool) -> "ExternalResource":
        """Perform the initialization of the resource.

        Parameters
        ----------
        is_local:
            True if a local version of the resource should be initialized, False
            otherwise. If the resource can't be initialized locally, can raise
            NotImplementedError. If is_local is False, this logic will be executed
            on the server.

        Returns
        -------
        An updated copy of the object
        """
        updated = self._do_activate(is_local)
        self._validate_transition(updated)
        if updated.status.state != ResourceState.ACTIVATING:
            raise IllegalStateTransitionError(
                "Calling .activate() should always leave the resource in the "
                "ACTIVATING state."
            )
        return updated

    def _do_activate(self) -> "ExternalResource":
        raise NotImplementedError(
            "Subclasses of ExternalResource should implement ._do_activate(is_local)"
        )

    @final
    def deactivate(self) -> "ExternalResource":
        """Clean up the resource.

        Returns
        -------
        An updated copy of the object
        """
        updated = self._do_deactivate()
        self._validate_transition(updated)
        if updated.status.state != ResourceState.DEACTIVATING:
            raise IllegalStateTransitionError(
                "Calling .deactivate() should always leave the resource in the "
                "DEACTIVATING state."
            )
        return updated

    def _do_deactivate(self) -> "ExternalResource":
        raise NotImplementedError(
            "Subclasses of ExternalResource should implement ._do_deactivate()"
        )

    def _validate_transition(self, updated: "ExternalResource"):
        updated = self._do_update()
        if (
            self.status.state != updated.status.state
            and not self.status.state.is_allowed_transition(updated.status.state)
        ):
            raise IllegalStateTransitionError(
                f"Cannout transition resource {self.id} from state "
                f"{self.status.state.name} to state: "
                f"{updated.status.state}"
            )
        if self.status.last_update_epoch_time > updated.status.last_update_epoch_time:
            raise IllegalStateTransitionError(
                f"Cannot change last_update_epoch_time to a time in the past. "
                f"Current update time: {self.status.last_update_epoch_time}. New "
                f"update time: {updated.status.last_update_epoch_time}"
            )

    @final
    def update(self) -> "ExternalResource":
        updated = self._do_update()
        self._validate_transition(updated)
        return updated

    def _do_update(self) -> "ExternalResource":
        raise NotImplementedError(
            "Subclasses of ExternalResource should implement _do_update"
        )
