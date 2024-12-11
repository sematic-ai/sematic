# Standard Library
from typing import List

# Third-party
import pytest

# Sematic
from sematic.abstract_function import FunctionError
from sematic.function import func
from sematic.runners.silent_runner import SilentRunner
from sematic.testing.mock_funcs import mock_sematic_funcs
from sematic.utils.exceptions import PipelineRunError


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
    with pytest.raises(PipelineRunError, match=r"Oh no.*") as exc_info:
        SilentRunner().run(pipeline())

    assert isinstance(exc_info.value.__context__, FunctionError)
    assert isinstance(exc_info.value.__context__.__context__, ValueError)

    with mock_sematic_funcs([remote_only_func]) as mock_funcs:
        mock_funcs[remote_only_func].mock.return_value = 1
        result = SilentRunner().run(pipeline())
        assert result == 5


def test_mock_sematic_funcs_use_original():
    with mock_sematic_funcs([remote_only_func, identity_func]) as mock_funcs:
        mock_funcs[remote_only_func].mock.return_value = 1
        mock_funcs[identity_func].mock.side_effect = mock_funcs[identity_func].original
        result = SilentRunner().run(pipeline())
        assert result == 5

        mock_funcs[identity_func].mock.assert_called()

    assert SilentRunner().run(identity_func(16)) == 16


def test_mock_sematic_funcs_still_type_checks():
    with pytest.raises(
        PipelineRunError,
        match=r".*remote_only_func.*",
    ) as exc_info:
        with mock_sematic_funcs([remote_only_func]) as mock_funcs:
            mock_funcs[remote_only_func].mock.return_value = "this is the wrong type!"
            SilentRunner().run(pipeline())

    # the exception occurs when casting the function's output value inside the resolver
    # it is not a FunctionError per se
    assert isinstance(exc_info.value.__context__, TypeError)
