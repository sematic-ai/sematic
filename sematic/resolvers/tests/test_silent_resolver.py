# Sematic
from sematic.resolvers.silent_resolver import SilentResolver
from sematic.calculator import func


@func
def add(a: float, b: float) -> float:
    return a + b


@func
def add3(a: float, b: float, c: float) -> float:
    return add(add(a, b), c)


@func
def pipeline(a: float, b: float) -> float:
    c = add(a, b)
    d = add3(a, b, c)
    return add(c, d)


def test_silent_resolver():
    assert SilentResolver().resolve(pipeline(3, 5)) == 24
