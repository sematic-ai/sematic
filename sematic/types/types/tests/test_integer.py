# Third-party
import pytest

# Sematic
from sematic.types.casting import can_cast_type, safe_cast
from sematic.types.serialization import (
    type_from_json_encodable,
    type_to_json_encodable,
    value_from_json_encodable,
    value_to_json_encodable,
)


@pytest.mark.parametrize(
    "value, expected_cast_value, expected_err_msg",
    (
        (1, 1, None),
        (1.23, 1, None),
        ("42", 42, None),
        ("abc", None, "Cannot cast 'abc' to <class 'int'>"),
    ),
)
def test_can_cast(value, expected_cast_value, expected_err_msg):
    cast_value, err_msg = safe_cast(value, int)
    assert cast_value == expected_cast_value
    if expected_err_msg is None:
        assert isinstance(cast_value, int)
    assert err_msg == expected_err_msg


@pytest.mark.parametrize(
    "from_type, can_cast, error",
    (
        (int, True, None),
        (float, True, None),
        (str, False, "Cannot cast <class 'str'> to int"),
    ),
)
def test_can_cast_type(from_type: type, can_cast: bool, error):
    assert can_cast_type(from_type, int) == (can_cast, error)


def test_json_serialization():
    serialized = value_to_json_encodable(42, int)

    assert serialized == 42

    deserialized = value_from_json_encodable(serialized, int)

    assert deserialized == 42
    assert isinstance(deserialized, int)


def test_type_to_json_encodable():
    assert type_to_json_encodable(int) == {
        "type": ("builtin", "int", {}),
        "registry": {"int": []},
    }


def test_type_from_json_encodable():
    json_encodable = type_to_json_encodable(int)
    assert type_from_json_encodable(json_encodable) is int
