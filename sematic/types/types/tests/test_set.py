# Standard Library
import sys
from typing import Dict, Optional, Set, Tuple, Union

# Third-party
import pytest

# Sematic
from sematic.types.casting import can_cast_type, safe_cast
from sematic.types.serialization import (
    get_json_encodable_summary,
    type_from_json_encodable,
    type_to_json_encodable,
    value_to_json_encodable,
)


@pytest.mark.parametrize(
    "type_, value, expected_cast_value, expected_error",
    (
        (Set[int], {1, 2, 3}, {1, 2, 3}, None),
        (Set[int], {1.2, 3.4}, {1, 3}, None),
        (Set[float], {"1.2", 3}, {1.2, 3}, None),
        (
            Set[float],
            {"abc"},
            None,
            (
                "Cannot cast {'abc'} to typing.Set[float]: "
                "Cannot cast 'abc' to <class 'float'>"
            ),
        ),
    ),
)
def test_safe_cast(type_, value, expected_cast_value, expected_error):
    cast_value, error = safe_cast(value, type_)

    assert cast_value == expected_cast_value
    assert error == expected_error


def test_summaries():
    summary, blobs = get_json_encodable_summary({1, 2, 3, 4, 5, 6, 7}, Set[int])
    assert summary == {
        "summary": [1, 2, 3, 4, 5, 6, 7],
        "length": 7,
    }
    assert blobs == {}

    long_value = 2**21 * "h"
    long_set = {long_value for _ in range(5)}
    summary, blobs = get_json_encodable_summary(long_set, Set[str])
    assert summary == {
        "summary": [long_value],
        "length": 1,
    }
    assert blobs == {}


CAN_CAST_TYPE_CASES = [
    (Set[float], Set[int], True, None),
    (
        float,
        Set[int],
        False,
        "Can't cast <class 'float'> to typing.Set[int]: not a subscripted generic",
    ),
    (Tuple[int, float], Set[float], True, None),
    (
        Tuple[Set[float], Set[int]],
        Set[Set[int]],
        True,
        None,
    ),
]

if sys.version_info >= (3, 9):
    CAN_CAST_TYPE_CASES.extend(
        [
            (set[float], Set[int], True, None),
            (Set[int], set[float], True, None),
            (set[int], set[int], True, None),
        ]
    )


@pytest.mark.parametrize(
    "from_type, to_type, expected_can_cast, expected_error",
    CAN_CAST_TYPE_CASES,
)
def test_can_cast_type(from_type, to_type, expected_can_cast, expected_error):
    can_cast, error = can_cast_type(from_type, to_type)
    assert can_cast is expected_can_cast
    assert error == expected_error


def test_type_to_json_encodable():
    type_ = Set[int]

    json_encodable = type_to_json_encodable(type_)

    assert json_encodable == {
        "type": ("typing", "set", {"args": [{"type": ("builtin", "int", {})}]}),
        "registry": {"int": [], "set": []},
    }


def test_type_to_json_encodable_subclass():
    type_ = Set[Optional[Dict[str, Union[int, float]]]]

    json_encodable = type_to_json_encodable(type_)

    assert json_encodable == {
        "type": (
            "typing",
            "set",
            {
                "args": [
                    {
                        "type": (
                            "typing",
                            "Union",
                            {
                                "args": [
                                    {
                                        "type": (
                                            "typing",
                                            "dict",
                                            {
                                                "args": [
                                                    {
                                                        "type": (
                                                            "builtin",
                                                            "str",
                                                            {},
                                                        )
                                                    },
                                                    {
                                                        "type": (
                                                            "typing",
                                                            "Union",
                                                            {
                                                                "args": [
                                                                    {
                                                                        "type": (
                                                                            "builtin",  # noqa: E501
                                                                            "int",
                                                                            {},
                                                                        ),
                                                                    },
                                                                    {
                                                                        "type": (
                                                                            "builtin",  # noqa: E501
                                                                            "float",  # noqa: E501
                                                                            {},
                                                                        ),
                                                                    },
                                                                ]
                                                            },
                                                        )
                                                    },
                                                ]
                                            },
                                        )
                                    },
                                    {"type": ("builtin", "NoneType", {})},
                                ]
                            },
                        )
                    },
                ]
            },
        ),
        "registry": {
            "str": [],
            "int": [],
            "float": [],
            "Union": [],
            "dict": [],
            "NoneType": [],
            "set": [],
        },
    }


def test_value_to_json_encodable():
    type_ = Set[int]

    json_encodable = value_to_json_encodable({1, 2, 3}, type_)

    assert json_encodable == [1, 2, 3]


@pytest.mark.parametrize(
    "type_",
    (Set[float], Set[Set[float]], Set[Optional[Dict[str, Union[int, float]]]]),
)
def test_type_from_json_encodable(type_):
    json_encodable = type_to_json_encodable(type_)
    assert type_from_json_encodable(json_encodable) == type_
