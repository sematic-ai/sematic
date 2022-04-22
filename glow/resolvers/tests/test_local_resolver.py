# Glow
from glow.calculator import calculator
from glow.resolvers.local_resolver import LocalResolver
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


def test_local_resolver():
    future = pipeline(3, 5)

    result = future.resolve(LocalResolver())

    assert result == 24
    assert isinstance(result, Float)
