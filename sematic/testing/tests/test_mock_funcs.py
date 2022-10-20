# Standard Library
from typing import List

# Sematic
from sematic.calculator import func
from sematic.testing.mock_funcs import mock_sematic_funcs


@func
def pipeline() -> int:
    return do_sum([remote_only_func(1), remote_only_func(2), identity_func(3)])


@func
def do_sum(ints: List[int]) -> int:
    return sum(ints)


@func
def remote_only_func(x: int) -> int:
    raise ValueError("Oh no! This function doesn't work when you're testing")


@func
def identity_func(x: int) -> int:
    return x


def test_mock_sematic_funcs():
    pass
