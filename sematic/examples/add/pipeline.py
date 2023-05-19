# Standard Library
import time

# Sematic
import sematic
from sematic.ee.metrics import log_metric


@sematic.func
def add(a: float, b: float) -> float:
    """
    Adds two numbers.
    """
    time.sleep(5)

    for i in range(10):
        log_metric("i", i)
        time.sleep(1)

    return a + b


@sematic.func
def add3(a: float, b: float, c: float) -> float:
    """
    Adds three numbers.
    """
    return add(add(a, b), c)


@sematic.func
def pipeline(a: float, b: float, c: float) -> float:
    """
    ## This is the docstring

    A trivial pipeline to showcase basic future encapsulation.

    This pipeline simply adds a bunch of numbers. It shows how functions can
    be arbitrarily nested.

    ### It supports markdown

    `pretty_cool`.
    """
    sum1 = add(a, b)
    sum2 = add(b, c)
    sum3 = add(a, c)
    return add3(sum1, sum2, sum3)
