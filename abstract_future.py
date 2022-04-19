"""
`AbstractFuture` is needed to resolve circular dependencies
between `Future` and `Resolver`.
"""
# Standard library
import abc
import enum
import typing
import uuid

# Glow
from glow.abstract_calculator import AbstractCalculator


class FutureState(enum.Enum):
    # The Future was just instantiated
    CREATED = "CREATED"
    # The Future was resolved and has a concrete
    # non-future value
    RESOLVED = "RESOLVED"
    # The future has executed and returned a nested future
    RAN = "RAN"
    # THe future was scheduled to execute
    SCHEDULED = "SCHEDULED"


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
        The input arguments to the calculator
    """

    def __init__(
        self, calculator: AbstractCalculator, kwargs: typing.Dict[str, typing.Any]
    ):
        self.calculator = calculator
        self.kwargs = kwargs
        self.id: str = uuid.uuid4().hex
        self.value: typing.Any = None
        self.state: FutureState = FutureState.CREATED
        self.parent_future: typing.Optional["AbstractFuture"] = None
        self.nested_future: typing.Optional["AbstractFuture"] = None
        self.inline: bool = False
