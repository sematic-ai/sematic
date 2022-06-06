"""
`AbstractFuture` is needed to resolve circular dependencies
between `Future` and `Resolver`.
"""
# Standard library
import abc
import enum
import typing
import uuid

# Sematic
from sematic.abstract_calculator import AbstractCalculator


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

    @classmethod
    def values(cls) -> typing.Tuple[str, ...]:
        return tuple([future_state.value for future_state in cls.__members__.values()])


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
        self, calculator: AbstractCalculator, kwargs: typing.Dict[str, typing.Any]
    ):
        self.id: str = uuid.uuid4().hex
        self.calculator = calculator
        self.kwargs = kwargs
        # We don't want to replace futures in kwargs, because it holds
        # the source of truth for the future graph. Instead we have concrete
        # values in resolved_kwargs
        # It will be set only once all input values are resolved
        self.resolved_kwargs: typing.Dict[str, typing.Any] = {}
        self.value: typing.Any = None
        self.state: FutureState = FutureState.CREATED
        self.parent_future: typing.Optional["AbstractFuture"] = None
        self.nested_future: typing.Optional["AbstractFuture"] = None
        self.inline: bool = False
        self.name: str = calculator.__name__
        self.tags: typing.List[str] = []
