import sematic


@sematic.func
def add(a: float, b: float) -> float:
    return a + b


@sematic.func
def pipeline(a: float, b: float) -> float:
    return add(add(a, b), add(a, b))
