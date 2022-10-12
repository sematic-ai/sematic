# Standard Library
import typing
from dataclasses import dataclass

# Sematic
import sematic


@dataclass
class Bar:
    barr: typing.List[int]


@dataclass
class Config:
    foo: typing.List[float]
    bar: Bar


@sematic.func
def using_dataclass(config: Config) -> Config:
    return config


@sematic.func
def add(a: float, b: float) -> float:
    """
    Adds two numbers.
    """
    return a + b


@sematic.func
def sum_list(list_: typing.List[float], a: float) -> float:  # type: ignore
    return sum(list_) + a


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

    This pipeline simply adds a bunch of numbers. It shows how calculators can
    be arbitrarily nested.

    ### It supports markdown

    `pretty_cool`.
    """
    sum1 = add(a, b)
    sum2 = add(b, c)
    sum3 = add(a, c)
    return add3(sum1, sum2, sum3)
