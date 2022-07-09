# Standard library
from typing import List

# Sematic
from sematic.future import Future
import sematic.future_operators.getitem  # # noqa: F401
from sematic.calculator import func


@func
def foo() -> List[str]:
    return ["foo", "bar", "bat"]


@func
def pipeline() -> str:
    return foo()[1]


def test_getitem():

    a = foo()[0]

    assert isinstance(a, Future)
    assert a.kwargs["key"] == 0
    assert a.calculator.output_type is str


def test_resolution():
    assert pipeline().resolve(tracking=False) == "bar"
