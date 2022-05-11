# Standard library
import logging

# Glow
from glow import calculator, OfflineResolver


@calculator
def add(a: float, b: float) -> float:
    return a + b


@calculator
def add3(a: float, b: float, c: float) -> float:
    return add(add(a, b), c)


@calculator
def pipeline(a: float, b: float, c: float) -> float:
    sum1 = add3(a, b, c)
    sum2 = add3(a, b, c)
    return add(sum1, sum2)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    future = pipeline(1, 2, 3)

    result = future.resolve(OfflineResolver())

    logging.info(result)
