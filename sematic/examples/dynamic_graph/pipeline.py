"""
This is the module in which you define your pipeline functions.

Feel free to break these definitions into as many files as you want for your
preferred code structure.
"""

# Standard Library
import random
import time
from typing import List

# Sematic
import sematic


@sematic.func
def random_uniform() -> float:
    return random.uniform(0, 1)


@sematic.func
def cube(data: float) -> float:
    time.sleep(data * 5)
    return data**3


@sematic.func
def square(data: float) -> float:
    time.sleep(data * 5)
    return data**2


@sematic.func
def process(data: float) -> float:
    if data > 0.5:
        return cube(data)

    return square(data)


@sematic.func
def find_best(randoms: List[float], candidates: List[float]) -> float:
    max_value = max(candidates)
    index = candidates.index(max_value)
    return randoms[index]


@sematic.func
def greater_than_09(winner: float) -> str:
    return "RARE EVENT: {}".format(winner)


@sematic.func
def lower_than_09(winner: float) -> str:
    return "MEH: {}".format(winner)


@sematic.func
def branch(winning_random: float) -> str:
    if winning_random > 0.9:
        return greater_than_09(winning_random)

    return lower_than_09(winning_random)


@sematic.func
def pipeline(ntries: int) -> str:
    """
    The root function of the pipeline.
    """
    squares = []
    randoms = []
    for i in range(ntries):
        value = random_uniform()
        randoms.append(value)
        squares.append(process(value))

    best = find_best(randoms, squares)

    return branch(best)
