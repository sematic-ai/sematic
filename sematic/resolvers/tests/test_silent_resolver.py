# Sematic
from sematic.calculator import func
from sematic.future_context import SematicContext, context
from sematic.resolvers.silent_resolver import SilentResolver


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


@func
def context_pipeline() -> SematicContext:
    return direct_context_func()


@func
def direct_context_func() -> SematicContext:
    return context()


def test_silent_resolver():
    assert SilentResolver().resolve(pipeline(3, 5)) == 24


def test_silent_resolver_context():
    future = context_pipeline()
    result = SilentResolver().resolve(future)
    assert result.root_id == future.id
    assert result.id != future.id

    future = direct_context_func()
    result = SilentResolver().resolve(future)
    assert result.root_id == future.id
    assert result.id == future.id
