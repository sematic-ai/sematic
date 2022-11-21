# Standard Library
import time

# Sematic
import sematic


@sematic.func(inline=False)
def add(a: float, b: float) -> float:
    time.sleep(5)
    return a + b


@sematic.func(inline=False)
def add3(a: float, b: float, c: float) -> float:
    return add(add(a, b), c)


@sematic.func(inline=False)
def fail() -> float:
    return fail_nested()


@sematic.func(inline=False)
def fail_nested() -> float:
    raise ValueError("Some exception")


@sematic.func(inline=True)
def pipeline(a: float, b: float, c: float) -> float:
    # return add(add3(a, b, c), add(a, b))
    # return add(a, b)
    return fail()
