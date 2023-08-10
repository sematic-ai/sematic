# Standard Library
import time

# Sematic
import sematic


@sematic.func(standalone=True)
def add(a: float, b: float) -> float:
    """
    Adds two numbers.
    """
    time.sleep(30)
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
    # sum2 = add(sum1, c)
    # sum3 = add(sum2, 0)
    # sum4 = add(sum3, 0)
    # sum5 = add(sum4, 0)
    # sum6 = add(sum5, 0)
    return add3(0, 0, sum1)
