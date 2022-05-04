# Glow
from glow.abstract_future import FutureState
from glow.calculator import calculator
from glow.db.tests.fixtures import test_db  # noqa: F401
from glow.db.queries import count_runs
from glow.resolvers.offline_resolver import OfflineResolver
from glow.types.types.float import Float
from glow.types.types.integer import Integer

# Testing mypy compliance
@calculator
def add_int(a: Integer, b: Integer) -> Integer:
    return a + b


@calculator
def add(a: Float, b: Float) -> Float:
    return a + b


@calculator
def add3(a: Float, b: Float, c: Float) -> Float:
    return add(add(a, b), c)


@calculator
def pipeline(a: Float, b: Float) -> Float:
    c = add(a, b)
    d = add3(a, b, c)
    return add(c, d)


def test_single_calculator(test_db):  # noqa: F811
    future = add(1, 2)
    assert future.resolve(OfflineResolver()) == 3
    assert future.state == FutureState.RESOLVED
    assert count_runs() == 1


def test_local_resolver(test_db):  # noqa: F811
    future = pipeline(3, 5)

    result = future.resolve(OfflineResolver())

    assert result == 24
    assert isinstance(result, Float)
    assert future.state == FutureState.RESOLVED

    assert count_runs() == 6
