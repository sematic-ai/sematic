# Standard library
from typing import Tuple

# Sematic
from sematic.future import Future
import sematic.future_operators.iter  # # noqa: F401
from sematic.calculator import func


@func
def foo() -> Tuple[int, str]:
    return 42, "foo"


@func
def pipeline() -> str:
    _, b = foo()

    return b


def test_iter():
    a, b = foo()

    assert isinstance(a, Future)
    assert a.kwargs["key"] == 0
    assert a.calculator.output_type is int

    assert isinstance(b, Future)
    assert b.kwargs["key"] == 1
    assert b.calculator.output_type is str


def test_resolution():
    assert pipeline().resolve(tracking=False) == "foo"
