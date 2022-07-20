# Standard library
from typing import Dict, List, Optional, Tuple, Union

# Third-party
import pytest

# Sematic
from sematic.types.casting import safe_cast, can_cast_type
from sematic.types.serialization import (
    type_from_json_encodable,
    value_to_json_encodable,
    type_to_json_encodable,
)


@pytest.mark.parametrize(
    "type_, value, expected_cast_value, expected_error",
    (
        (List[int], [1, 2, 3], [1, 2, 3], None),
        (List[int], [1.2, 3.4], [1, 3], None),
        (List[float], ["1.2", 3], [1.2, 3], None),
        (
            List[float],
            ["abc"],
            None,
            (
                "Cannot cast ['abc'] to typing.List[float]: "
                "Cannot cast 'abc' to <class 'float'>"
            ),
        ),
    ),
)
def test_safe_cast(type_, value, expected_cast_value, expected_error):
    cast_value, error = safe_cast(value, type_)

    assert cast_value == expected_cast_value
    assert error == expected_error


@pytest.mark.parametrize(
    "from_type, to_type, expected_can_cast, expected_error",
    (
        (List[float], List[int], True, None),
        # Need to implement str casting logic
        # (List[float], List[str], True, None),
        (
            float,
            List[int],
            False,
            "Can't cast <class 'float'> to typing.List[int]: not a subscripted generic",
        ),
        (Tuple[int, float], List[float], True, None),
        (
            Tuple[List[float], List[int]],
            List[List[int]],
            True,
            None,
        ),
    ),
)
def test_can_cast_type(from_type, to_type, expected_can_cast, expected_error):
    can_cast, error = can_cast_type(from_type, to_type)
    assert can_cast is expected_can_cast
    assert error == expected_error


def test_type_to_json_encodable():
    type_ = List[int]

    json_encodable = type_to_json_encodable(type_)

    assert json_encodable == {
        "type": ("typing", "list", {"args": [{"type": ("builtin", "int", {})}]}),
        "registry": {"int": [], "list": []},
    }


def test_type_to_json_encodable_subclass():
    type_ = List[Optional[Dict[str, Union[int, float]]]]

    json_encodable = type_to_json_encodable(type_)

    assert json_encodable == {
        "type": (
            "typing",
            "list",
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
            "list": [],
        },
    }


def test_value_to_json_encodable():
    type_ = List[int]

    json_encodable = value_to_json_encodable([1, 2, 3], type_)

    assert json_encodable == [1, 2, 3]


# Needs to be defined here intead of inside test_to_binary_arbitrary
# to make sure pickling is deterministic
class A:
    pass


def test_to_binary_arbitrary():

    type_ = List[A]

    json_encodable = value_to_json_encodable([A(), A()], type_)

    assert json_encodable == [
        {
            "pickle": "gAWVMAAAAAAAAACMI3NlbWF0aWMudHlwZXMudHlwZXMudGVzdHMudGVzdF9saXN0lIwBQZSTlCmBlC4="  # noqa: E501
        },
        {
            "pickle": "gAWVMAAAAAAAAACMI3NlbWF0aWMudHlwZXMudHlwZXMudGVzdHMudGVzdF9saXN0lIwBQZSTlCmBlC4="  # noqa: E501
        },
    ]


@pytest.mark.parametrize(
    "type_",
    (List[float], List[List[float]], List[Optional[Dict[str, Union[int, float]]]]),
)
def test_type_from_json_encodable(type_):
    json_encodable = type_to_json_encodable(type_)
    assert type_from_json_encodable(json_encodable) is type_
