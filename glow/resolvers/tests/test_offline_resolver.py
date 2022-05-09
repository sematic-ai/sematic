# Glow
from glow.abstract_future import FutureState
from glow.calculator import calculator
from glow.db.tests.fixtures import test_db  # noqa: F401
from glow.db.queries import count_runs
from glow.resolvers.offline_resolver import OfflineResolver


# Testing mypy compliance
@calculator
def add_int(a: int, b: int) -> int:
    return a + b


@calculator
def add(a: float, b: float) -> float:
    return a + b


@calculator
def add3(a: float, b: float, c: float) -> float:
    return add(add(a, b), c)


@calculator
def pipeline(a: float, b: float) -> float:
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
    assert isinstance(result, float)
    assert future.state == FutureState.RESOLVED

    assert count_runs() == 6
