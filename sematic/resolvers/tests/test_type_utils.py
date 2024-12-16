# Standard Library
from typing import Any, List, Union


try:
    # Python 3.9
    # Standard Library
    from types import GenericAlias  # type: ignore
except ImportError:
    # Python 3.8
    from typing import _GenericAlias as GenericAlias  # type: ignore

# Third-party
import pytest

# Sematic
from sematic.resolvers.type_utils import make_list_type, make_tuple_type


@pytest.mark.parametrize(
    "list_, expected_type",
    (
        ([], List[Any]),
        ([1, 2], List[int]),
        ([1, 2.0], List[Union[int, float]]),
        ([1, "foo", True], List[Union[int, str, bool]]),
    ),
)
def test_make_list_type(list_, expected_type):
    assert make_list_type(list_) == expected_type


@pytest.mark.parametrize(
    "tuple_, expected_type",
    (
        ((1, 2), GenericAlias(tuple, (int, int))),
        ((1, 2.0), GenericAlias(tuple, (int, float))),
        ((1, 2, "foo"), GenericAlias(tuple, (int, int, str))),
    ),
)
def test_make_tuple_type(tuple_, expected_type):
    assert make_tuple_type(tuple_) == expected_type
