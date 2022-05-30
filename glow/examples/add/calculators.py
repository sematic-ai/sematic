# Standrd library
from dataclasses import dataclass
import time

# Glow
from glow import calculator
from glow.types import FloatInRange


@dataclass
class Bar:
    barr: list[int]


@dataclass
class Config:
    foo: list[float]
    bar: Bar


@calculator
def using_dataclass(config: Config) -> Config:
    return config


@calculator
def add(a: float, b: float) -> float:
    """
    Adds two numbers.
    """
    time.sleep(5)
    return a + b


@calculator
def sum_list(list_: list[float], a: FloatInRange[0, 1]) -> float:  # type: ignore
    return sum(list_) + a


@calculator
def add3(a: float, b: float, c: float) -> float:
    """
    Adds three numbers.
    """
    time.sleep(5)
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
    time.sleep(5)
    sum1 = add3(a, b, c)
    sum2 = add3(a, b, c)
    return add(sum1, sum2)
