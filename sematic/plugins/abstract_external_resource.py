# Standard Library
import logging
import time
import uuid
from dataclasses import dataclass, field, fields, replace
from enum import Enum, unique
from typing import TypeVar, final

# Sematic
from sematic.abstract_future import AbstractFuture
from sematic.future_context import SematicContext, context
from sematic.utils.exceptions import (
    IllegalStateTransitionError,
    IllegalUseOfFutureError,
    NotInSematicFuncError,
)

logger = logging.getLogger(__name__)


@unique
class ResourceState(Enum):
    """Represents the state of an external resource.

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
    DEACTIVATED:
        The resource has been deactivated and may not even exist anymore.
        It is not usable.
    """

    CREATED = "CREATED"
    ACTIVATING = "ACTIVATING"
    ACTIVE = "ACTIVE"
    DEACTIVATING = "DEACTIVATING"
    DEACTIVATED = "DEACTIVATED"

    def is_allowed_transition(self, other_state: "ResourceState") -> bool:
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
        # Created -> Deactivated: after creating the resource,
        # but before starting to activate it, it was decided
        # to not activate the resource after all. Since no activation
        # was performed, there is no need to do anything for deactivation
        # so we can skip DEACTIVATING.
        ResourceState.DEACTIVATED,
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
        # Deactivating -> Deactivated: normal progression for deactivation
        ResourceState.DEACTIVATED,
    },
    ResourceState.DEACTIVATED: {},
}


@unique
class ManagedBy(Enum):
    """Represents what entity is managing the state of the resource

    Attributes
    ----------
    RESOLVER:
        The resource's state is being managed by the resolver.
    SERVER:
        The resource's state is being managed by the server.
    UNKNOWN:
        It's unknown what entity is managing the resource's state. Can only
        be used when resource is in the CREATED state.
    """

    RESOLVER = "RESOLVER"
    SERVER = "SERVER"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class ResourceStatus:
    """The status of the resource.

    Attributes
    ----------
    state:
        The discrete state that the resource is in
    message:
        A human-readable message about why the resource entered this state
    last_update_epoch_time:
        The last time this status was checked against the actual external resource
    managed_by:
        Whether the resource is managed locally, remotely, or not known.
    """

    state: ResourceState
    message: str
    last_update_epoch_time: int = field(
        default_factory=lambda: int(time.time()), compare=False
    )
    managed_by: ManagedBy = ManagedBy.UNKNOWN

    def __post_init__(self):
        if (
            self.state not in {ResourceState.CREATED, ResourceState.DEACTIVATED}
            and self.managed_by == ManagedBy.UNKNOWN
        ):
            raise IllegalStateTransitionError(
                "Only resources in the CREATED and DEACTIVATED states "
                "can have managed_by==UNKNOWN"
            )


T = TypeVar("T")


@dataclass(frozen=True)
class AbstractExternalResource:
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
        )
    )

    def __post_init__(self):
        for field_ in fields(self):
            field_value = getattr(self, field_.name)
            if isinstance(field_value, AbstractFuture):
                func_name = {field_value.calculator.__name__}
                type_name = type(self).__name__
                raise IllegalUseOfFutureError(
                    f"Tried to instantiate {type_name} with a future for the "
                    f"value of the field '{field_.name}'. The future appears to be the "
                    f"return value from a call to '{func_name}'. "
                    f"If you wish to use {type_name} downstream from "
                    f"'{func_name}', consider wrapping the code "
                    f"using {type_name} in a new Sematic func and passing the "
                    f"output of {func_name} to that new func."
                )
        try:
            uuid.UUID(hex=self.id)
        except ValueError:
            raise ValueError(f"ExternalResource had an invalid uuid: '{self.id}'")
        if not isinstance(self.status, ResourceStatus):
            raise ValueError(f"ExternalResource had invalid status: '{self.status}'")

    @final
    def activate(self, is_local: bool) -> "AbstractExternalResource":
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
        logger.debug("Activating %s", self)
        managed_by_updated = replace(
            self,
            status=replace(
                self.status,
                managed_by=ManagedBy.RESOLVER if is_local else ManagedBy.SERVER,
                last_update_epoch_time=int(time.time()),
            ),
        )
        updated = managed_by_updated._do_activate(is_local)
        self.validate_transition(updated)
        if updated.status.state != ResourceState.ACTIVATING:
            raise IllegalStateTransitionError(
                "Calling .activate() did not leave the resource in the "
                "ACTIVATING state."
            )
        return updated

    def _do_activate(self, is_local: bool) -> "AbstractExternalResource":
        raise NotImplementedError(
            "Subclasses of ExternalResource should implement ._do_activate(is_local)"
        )

    @final
    def deactivate(self) -> "AbstractExternalResource":
        """Clean up the resource.

        Returns
        -------
        An updated copy of the object
        """
        if self.status.state == ResourceState.CREATED:
            logger.warning(
                "Deactivating resource before it was ever activated: %s", self.id
            )
            updated = replace(
                self,
                status=replace(
                    self.status,
                    state=ResourceState.DEACTIVATED,
                    message="Resource activation was canceled.",
                    last_update_epoch_time=int(time.time()),
                ),
            )
        else:
            logger.debug("Deactivating %s", self)
            updated = self._do_deactivate()
            if updated.status.state != ResourceState.DEACTIVATING:
                raise IllegalStateTransitionError(
                    "Calling .deactivate() did not leave the resource in the "
                    "DEACTIVATING state."
                )
        self.validate_transition(updated)
        return updated

    def _do_deactivate(self) -> "AbstractExternalResource":
        raise NotImplementedError(
            "Subclasses of ExternalResource should implement ._do_deactivate()"
        )

    def validate_transition(self, updated: "AbstractExternalResource"):
        """Confirm that the resource can go from its current state to the updated one.

        Parameters
        ----------
        updated:
            The new version of the resource

        Raises
        ------
        IllegalStateTransitionError:
            If the transition is not allowed
        """
        if self.id != updated.id:
            raise IllegalStateTransitionError(
                f"Cannot change id of resource from {self.id} to " f"{updated.id}"
            )
        if (
            self.status.state != updated.status.state
            and not self.status.state.is_allowed_transition(updated.status.state)
        ):
            raise IllegalStateTransitionError(
                f"Cannot transition resource {self.id} from state "
                f"{self.status.state.name} to state: "
                f"{updated.status.state.name}"
            )
        if self.status.last_update_epoch_time > updated.status.last_update_epoch_time:
            raise IllegalStateTransitionError(
                f"Cannot change last_update_epoch_time to a time in the past. "
                f"Current update time: {self.status.last_update_epoch_time}. New "
                f"update time: {updated.status.last_update_epoch_time}"
            )
        if (
            self.status.managed_by != updated.status.managed_by
            and self.status.managed_by != ManagedBy.UNKNOWN
        ):
            raise IllegalStateTransitionError(
                f"Cannot change managed_by once it is no longer UNKNOWN"
                f"Current managed_by: {self.status.managed_by}. New "
                f"managed_by: {updated.status.managed_by}"
            )

    @final
    def update(self) -> "AbstractExternalResource":
        """Query the external resource for any updates and return the updated object.

        If no properties have changed since the last time update was called, the object
        should be returned as-is, except for the `status.last_updated_epoch_time` property
        (which should be set to the current epoch time).

        Returns
        -------
        A clone of this object with any changes in state applied.
        """
        logger.debug("Updating %s", self)
        updated = self._do_update()
        updated = replace(
            updated,
            status=replace(updated.status, last_update_epoch_time=int(time.time())),
        )
        self.validate_transition(updated)
        return updated

    def _do_update(self) -> "AbstractExternalResource":
        raise NotImplementedError(
            "Subclasses of ExternalResource should implement _do_update"
        )

    # type annotation with the type var so mypy knows that
    # what is returned is an instance of the same subclass
    # as is used when entering the 'with' context.
    def __enter__(self: T) -> T:
        try:
            ctx: SematicContext = context()
        except NotInSematicFuncError:
            raise NotInSematicFuncError(
                f"Called `with {type(self).__name__}(...)`, but the call was not "
                f"made while executing a Sematic func."
            )
        try:
            updated = ctx.private.load_resolver_class().activate_resource_for_run(
                resource=self, run_id=ctx.run_id, root_id=ctx.root_id
            )
            if updated.status.state != ResourceState.ACTIVE:
                raise IllegalStateTransitionError(
                    f"Resolver {ctx.private.load_resolver_class()} failed to "
                    f"activate {updated}."
                )
            ctx.private.load_resolver_class().entering_resource_context(
                resource=updated
            )
            return updated
        except Exception:
            self.__exit__()  # type: ignore
            raise

    def __exit__(self, exc_type=None, exc_value=None, exc_traceback=None):
        ctx: SematicContext = context()
        ctx.private.load_resolver_class().exiting_resource_context(self.id)
        deactivated = ctx.private.load_resolver_class().deactivate_resource(self.id)
        if deactivated.status.state != ResourceState.DEACTIVATED:
            raise IllegalStateTransitionError(
                f"Resolver {ctx.private.load_resolver_class()} failed to "
                f"deactivate {deactivated}."
            )
