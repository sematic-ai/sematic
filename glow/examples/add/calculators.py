# Standrd library
import time

# Glow
from glow import calculator


@calculator
def add(a: float, b: float) -> float:
    time.sleep(5)
    return a + b


@calculator
def add3(a: float, b: float, c: float) -> float:
    return add(add(a, b), c)


@calculator
def pipeline(a: float, b: float, c: float) -> float:
    """
    ## This is the docstring

    A trivial pipeline to showcase basic future encapsulation.

    This pipeline simply adds a bunch of numbers. It shows how calculators can
    be arbitrarily nested.

    ### It supports markdown

    `pretty_cool`.
    """
    sum1 = add3(a, b, c)
    sum2 = add3(a, b, c)
    return add(sum1, sum2)
