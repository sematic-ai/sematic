# Standard Library
import hashlib
from typing import Dict, List, Optional, Tuple, Union

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
from sematic.types.types.image import Image


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


def test_summaries():
    summary, blobs = get_json_encodable_summary([1, 2, 3, 4, 5, 6, 7], List[int])
    assert summary == {
        "summary": [1, 2, 3, 4, 5, 6, 7],
        "length": 7,
    }
    assert blobs == {}

    long_value = 2**21 * "h"
    long_list = [long_value for _ in range(5)]
    summary, blobs = get_json_encodable_summary(long_list, List[str])
    assert summary == {
        "summary": [long_value],
        "length": 5,
    }
    assert blobs == {}


def test_blob_summary():
    bytes_ = b"foobar"
    blob_id = hashlib.sha1(bytes_).hexdigest()
    image = Image(bytes=bytes_)
    list_ = [image] * 5
    summary, blobs = get_json_encodable_summary(list_, List[Image])

    assert summary == {
        "summary": [{"mime_type": "text/plain", "bytes": {"blob": blob_id}}] * 5,
        "length": 5,
    }

    assert blobs == {blob_id: bytes_}


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
