"""
`AbstractFuture` is needed to resolve circular dependencies
between `Future` and `Resolver`.
"""
# Standard Library
import abc
import enum
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

# Sematic
from sematic.abstract_calculator import AbstractCalculator
from sematic.external_resource import ExternalResource, ResourceState
from sematic.future_context import NotInSematicFuncError, context
from sematic.resolvers.resource_requirements import ResourceRequirements
from sematic.retry_settings import RetrySettings


class FutureState(enum.Enum):
    # The Future was just instantiated
    CREATED = "CREATED"
    # The Future was resolved and has a concrete
    # non-future value
    RESOLVED = "RESOLVED"
    # The future has executed and returned a nested future
    RAN = "RAN"
    # The future was scheduled to execute
    SCHEDULED = "SCHEDULED"
    FAILED = "FAILED"
    NESTED_FAILED = "NESTED_FAILED"
    # The future failed and is being queued for retrying
    RETRYING = "RETRYING"
    CANCELED = "CANCELED"

    @classmethod
    def as_object(cls, future_state: Union[str, "FutureState"]) -> "FutureState":
        """Return the provided argument as a FutureState

        Parameters
        ----------
        future_state:
            Either an instance of FutureState or a string key for FutureState

        Returns
        -------
        The given object if it was already a FutureState. Otherwise uses the object
        as a key to lookup the correct FutureState.
        """
        if isinstance(future_state, FutureState):
            return future_state
        return FutureState[future_state]

    @classmethod
    def values(cls) -> Tuple[str, ...]:
        return tuple([future_state.value for future_state in cls.__members__.values()])

    def is_terminal(self):
        """Return True if & only if the state represents one that can't be moved from"""
        return self in _TERMINAL_STATES


_TERMINAL_STATES = {
    FutureState.NESTED_FAILED,
    FutureState.FAILED,
    FutureState.RESOLVED,
    FutureState.CANCELED,
}


@dataclass
class FutureProperties:
    """
    This is meant as a container of properties for Future.

    The reason is we want to keep the property namespace as empty
    as possible on Future to enable attribute access on futures
    of dataclasses and such.

    Ideally over time we move all future properties to this dataclass.
    """

    inline: bool
    name: str
    tags: List[str]
    kwargs: Dict[str, Any]
    resource_requirements: Optional[ResourceRequirements] = None
    retry_settings: Optional[RetrySettings] = None
    base_image_tag: Optional[str] = None
    external_resources: List[ExternalResource] = field(default_factory=list)

    def get_resolved_kwargs(self) -> Dict[str, Any]:
        """
        Extract only resolved/concrete kwargs.

        For external resources, only ones in the ACTIVE state can be used
        and are considered resolved.
        """
        resources_by_id = {r.id: r for r in self.external_resources}
        resolved_kwargs = {}
        for name, value in self.kwargs.items():
            if isinstance(value, AbstractFuture):
                if value.state == FutureState.RESOLVED:
                    resolved_kwargs[name] = value.value
            elif isinstance(value, ExternalResource):
                value = resources_by_id.get(value.id)
                if value.status.state == ResourceState.ACTIVE:
                    resolved_kwargs[name] = value
            else:
                resolved_kwargs[name] = value

        return resolved_kwargs

    def all_args_ready(self) -> bool:
        """True if all args are sufficiently ready for the future to be scheduled.

        External resources are scheduled along with the future and thus need not be
        active for this to return True.
        """
        missing_kwarg_keys = set(self.kwargs.keys()).difference(
            self.get_resolved_kwargs().keys()
        )
        for key in missing_kwarg_keys:
            value = self.kwargs[key]
            if not isinstance(value, ExternalResource):
                # it's ok if there are args that aren't usable yet
                # if they're external resources. Those will get scheduled
                # along with the future.
                return False
        return True


class AbstractFuture(abc.ABC):
    """
    Abstract base class to support `Future`.

    This is necessary for two reasons:
    - Resolve dependency loops (notably Future depends on LocalResolver)
    - Enabling MyPy compliance in functions that take futures as inputs

    What should go into `AbstractFuture` vs. `Future`?
    In general, as much as possible should go into `AbstractFuture` without:
    - introducing dependency cycles
    - actual logic (e.g. resolve)

    Parameters
    ----------
    calculator: AbstractCalculator
        The calculator this is a future of
    kwargs: typing.Dict[str, typing.Any]
        The input arguments to the calculator. Can be concrete values or other futures.
    """

    def __init__(
        self,
        calculator: AbstractCalculator,
        kwargs: Dict[str, Any],
        inline: bool,
        resource_requirements: Optional[ResourceRequirements] = None,
        retry_settings: Optional[RetrySettings] = None,
        base_image_tag: Optional[str] = None,
    ):
        self.id: str = make_future_id()
        self.calculator = calculator
        self.value: Any = None
        self.state: FutureState = FutureState.CREATED
        self.parent_future: Optional["AbstractFuture"] = None
        self.nested_future: Optional["AbstractFuture"] = None

        try:
            external_resources: List[ExternalResource] = list(
                context().private.external_resources  # type: ignore
            )
        except NotInSematicFuncError:
            # the root future is not created inside another func
            external_resources = []

        # checks in future_context should ensure that this passes
        # see: https://github.com/sematic-ai/sematic/issues/388
        assert len(external_resources) <= 1

        self._props = FutureProperties(
            inline=inline,
            resource_requirements=resource_requirements,
            retry_settings=retry_settings,
            name=calculator.__name__,
            kwargs=kwargs,
            tags=[],
            base_image_tag=base_image_tag,
            external_resources=external_resources,
        )

    @property
    def props(self) -> FutureProperties:
        """
        Ideally this is the only property we expose on future.
        All other properties above should be migrated to FutureProperties

        TODO: Migrate all future properties to FutureProperties
        """
        return self._props

    @property
    def kwargs(self) -> Dict[str, Any]:
        """The keyword arguments to pass into the Sematic func at execition time.

        May contain Futures for argument values.
        """
        return self._props.kwargs

    def __repr__(self):
        parent_id = self.parent_future.id if self.parent_future is not None else None
        nested_id = self.nested_future.id if self.nested_future is not None else None
        return (
            f"Future(id={self.id}, func={self.calculator}, "
            f"state={self.state.value}, parent_id={parent_id}, "
            f"nested_id={nested_id}, value={self.value})"
        )


def make_future_id() -> str:
    return uuid.uuid4().hex
