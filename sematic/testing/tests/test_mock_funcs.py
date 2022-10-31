# Standard Library
from typing import List

import pytest

# Sematic
from sematic.abstract_calculator import CalculatorError
from sematic.calculator import func
from sematic.resolvers.silent_resolver import SilentResolver
from sematic.testing.mock_funcs import mock_sematic_funcs
from sematic.utils.exceptions import ResolutionError


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
    with pytest.raises(ResolutionError, match=r"Oh no.*") as exc_info:
        pipeline().resolve(SilentResolver())

    assert isinstance(exc_info.value.__context__, CalculatorError)
    assert isinstance(exc_info.value.__context__.__context__, ValueError)

    with mock_sematic_funcs([remote_only_func]) as mock_funcs:
        mock_funcs[remote_only_func].mock.return_value = 1
        result = pipeline().resolve(SilentResolver())
        assert result == 5


def test_mock_sematic_funcs_use_original():
    with mock_sematic_funcs([remote_only_func, identity_func]) as mock_funcs:
        mock_funcs[remote_only_func].mock.return_value = 1
        mock_funcs[identity_func].mock.side_effect = mock_funcs[identity_func].original
        result = pipeline().resolve(SilentResolver())
        assert result == 5

        mock_funcs[identity_func].mock.assert_called()

    assert identity_func(16).resolve(SilentResolver()) == 16


def test_mock_sematic_funcs_still_type_checks():
    with pytest.raises(
        ResolutionError,
        match=r"for 'sematic.testing.tests.test_mock_funcs.remote_only_func'.*",
    ) as exc_info:

        with mock_sematic_funcs([remote_only_func]) as mock_funcs:
            mock_funcs[remote_only_func].mock.return_value = "this is the wrong type!"
            pipeline().resolve(SilentResolver())

    # the exception occurs when casting the function's output value inside the resolver
    # it is not a CalculatorError per se
    assert isinstance(exc_info.value.__context__, TypeError)
