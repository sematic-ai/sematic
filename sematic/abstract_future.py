"""
`AbstractFuture` is needed to resolve circular dependencies
between `Future` and `Resolver`.
"""
# Standard Library
import abc
import enum
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, FrozenSet, List, Optional, Tuple, Union

# Sematic
from sematic.abstract_calculator import AbstractCalculator
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
        """Return the provided argument as a FutureState.

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
        """Return True if & only if the state represents one that can't be moved from."""
        return self in _TERMINAL_STATES

    @classmethod
    def terminal_states(cls) -> FrozenSet["FutureState"]:
        return _TERMINAL_STATES

    @classmethod
    def failure_terminal_states(cls) -> FrozenSet["FutureState"]:
        return _FAILURE_TERMINAL_STATES

    @classmethod
    def terminal_state_strings(cls) -> FrozenSet[str]:
        return _TERMINAL_STATE_STRINGS

    @classmethod
    def is_allowed_transition(
        cls,
        from_status: Optional[Union["FutureState", str]],
        to_status: Union["FutureState", str],
    ) -> bool:
        if isinstance(from_status, str):
            from_status = FutureState[from_status]
        if isinstance(to_status, str):
            to_status = FutureState[to_status]
        return to_status in _ALLOWED_TRANSITIONS[from_status]


_ALLOWED_TRANSITIONS = {
    None: frozenset({FutureState.CREATED}),
    FutureState.CREATED: frozenset(
        {
            FutureState.SCHEDULED,
            # Not all that uncommon: if run is downstream from something that
            # is canceled/failed, it goes from CREATED -> CANCELLED
            FutureState.CANCELED,
        }
    ),
    FutureState.SCHEDULED: frozenset(
        {
            FutureState.RAN,
            FutureState.RETRYING,
            FutureState.CANCELED,
            FutureState.RESOLVED,
            # TODO: remove (See https://github.com/sematic-ai/sematic/issues/609)
            FutureState.FAILED,
        }
    ),
    FutureState.RAN: frozenset(
        {FutureState.NESTED_FAILED, FutureState.RESOLVED, FutureState.CANCELED}
    ),
    FutureState.RETRYING: frozenset(
        {FutureState.FAILED, FutureState.SCHEDULED, FutureState.CANCELED}
    ),
    FutureState.FAILED: frozenset(
        {
            # TODO: remove (See https://github.com/sematic-ai/sematic/issues/609)
            FutureState.RETRYING
        }
    ),
    FutureState.NESTED_FAILED: frozenset(),
    FutureState.CANCELED: frozenset(),
    FutureState.RESOLVED: frozenset(),
}


_TERMINAL_STATES = frozenset(
    {
        FutureState.NESTED_FAILED,
        FutureState.FAILED,
        FutureState.RESOLVED,
        FutureState.CANCELED,
    }
)

_FAILURE_TERMINAL_STATES = frozenset({FutureState.FAILED, FutureState.NESTED_FAILED})

_TERMINAL_STATE_STRINGS = frozenset(state.value for state in _TERMINAL_STATES)


@dataclass
class FutureProperties:
    """
    This is meant as a container of properties for Future.

    The reason is we want to keep the property namespace as empty
    as possible on Future to enable attribute access on futures
    of dataclasses and such.

    Ideally over time we move all future properties to this dataclass.
    """

    standalone: bool
    name: str
    tags: List[str]
    state: FutureState
    cache: bool = False
    resource_requirements: Optional[ResourceRequirements] = None
    retry_settings: Optional[RetrySettings] = None
    base_image_tag: Optional[str] = None
    timeout_minutes: Optional[int] = None
    scheduled_epoch_time: Optional[float] = None

    def __post_init__(self):
        if self.timeout_minutes is None:
            return
        if int(self.timeout_minutes) != self.timeout_minutes:
            raise ValueError(
                f"Timeouts must be an integer number "
                f"of minutes, got: {self.timeout_minutes}"
            )
        if self.timeout_minutes < 1:
            raise ValueError(
                f"Timeouts must be >=1 minutes, got: {self.timeout_minutes}"
            )

    @property
    def remaining_timeout_seconds(self) -> Optional[float]:
        """Number of seconds until timeout, or None if undefined

        Seconds until timeout is defined as the difference between
        the total allowed time and the time the future has spent
        in the SCHEDULED or RAN states so far. Can be negative if
        timeout is expired.
        """
        if self.scheduled_epoch_time is None:
            return None
        if self.timeout_minutes is None:
            return None
        if self.state.is_terminal():
            return None
        time_so_far = time.time() - self.scheduled_epoch_time
        return self.timeout_minutes * 60 - time_so_far


class AbstractFuture(abc.ABC):
    """
    Abstract base class to support `Future`.

    This is necessary for two reasons: - Resolve dependency loops (notably
    Future depends on LocalResolver) - Enabling MyPy compliance in functions
    that take futures as inputs

    What should go into `AbstractFuture` vs. `Future`? In general, as much as
    possible should go into `AbstractFuture` without:
    - introducing dependency cycles
    - actual logic (e.g. resolve)

    Parameters
    ----------
    calculator: AbstractCalculator
        The calculator this is a future of.
    kwargs: Dict[str, Any]
        The input arguments to the calculator. Can be concrete values or other
        futures.
    standalone: bool
        When using the `CloudResolver`, whether the instrumented function should
        be executed as a standalone Kubernetes job or inside the same process
        and worker that is executing the `Resolver` itself.
    original_future_id: Optional[str]
        The id of the original future this future was cloned from, if any.
    cache: bool
        Whether to cache the function's output value under the `cache_namespace`
        configured in the `Resolver`. Defaults to `False`.

        Do not activate this on a non-deterministic function!
    resource_requirements: Optional[ResourceRequirements]
        When using the `CloudResolver`, specifies what special execution
        resources the function requires. Defaults to `None`.
    retry_settings: Optional[RetrySettings]
        Specifies in case of which Exceptions the function's execution should be
        retried, and how many times. Defaults to `None`.
    timeout_minutes:
        Specified how many minutes are allowed to be spent between the future entering the
        SCHEDULED state and entering some terminal state.
    """

    def __init__(
        self,
        calculator: AbstractCalculator,
        kwargs: Dict[str, Any],
        standalone: bool,
        original_future_id: Optional[str] = None,
        cache: bool = False,
        resource_requirements: Optional[ResourceRequirements] = None,
        retry_settings: Optional[RetrySettings] = None,
        base_image_tag: Optional[str] = None,
        timeout_minutes: Optional[int] = None,
    ):
        self.id: str = make_future_id()
        self.original_future_id = original_future_id
        self.calculator = calculator
        self.kwargs = kwargs
        # We don't want to replace futures in kwargs, because it holds
        # the source of truth for the future graph. Instead, we have concrete
        # values in resolved_kwargs
        # It will be set only once all input values are resolved
        self.resolved_kwargs: Dict[str, Any] = {}
        self.value: Any = None
        self.parent_future: Optional["AbstractFuture"] = None
        self.nested_future: Optional["AbstractFuture"] = None

        self._props = FutureProperties(
            standalone=standalone,
            cache=cache,
            state=FutureState.CREATED,
            resource_requirements=resource_requirements,
            retry_settings=retry_settings,
            name=calculator.__name__,
            tags=[],
            base_image_tag=base_image_tag,
            timeout_minutes=timeout_minutes,
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
    def state(self) -> FutureState:
        return self._props.state

    @state.setter
    def state(self, state: FutureState) -> None:
        self._props.state = state
        if state is FutureState.SCHEDULED and self.props.scheduled_epoch_time is None:
            self._props.scheduled_epoch_time = time.time()
        if state.is_terminal() or state is FutureState.RETRYING:
            # ensures that timeout resets for retries.
            self._props.scheduled_epoch_time = None

    def __repr__(self):
        parent_id = self.parent_future.id if self.parent_future is not None else None
        nested_id = self.nested_future.id if self.nested_future is not None else None
        return (
            f"Future(id={self.id}, func={self.calculator}, "
            f"state={self.state.value}, parent_id={parent_id}, "
            f"nested_id={nested_id}, value={self.value})"
        )

    def is_root_future(self):
        """
        Returns whether this is the root Future of a pipeline Resolution.
        """
        return self.parent_future is None


def make_future_id() -> str:
    return uuid.uuid4().hex


def get_minimum_call_chain_timeout_seconds(
    future: AbstractFuture,
) -> Tuple[Optional[float], Optional[AbstractFuture]]:
    """Given a future, determine the most restrictive timeout up its call chain.

    Parameters
    ----------
    future:
        The future to start traversal at.

    Returns
    -------
    If no futures up the call chain for this future have active timeouts,
    returns (None, None). Otherwise returns a tuple where the first element
    is the time until the most restrictive timeout expires and
    the second element is the future that had specified that timeout.
    """
    call_chain = [future]
    while call_chain[-1].parent_future is not None:
        call_chain.append(call_chain[-1].parent_future)

    remaining_time_future_pairs = [
        (future.props.remaining_timeout_seconds, future)
        for future in call_chain
        if future.props.remaining_timeout_seconds is not None
    ]

    if len(remaining_time_future_pairs) == 0:
        return None, None

    return min(remaining_time_future_pairs)
