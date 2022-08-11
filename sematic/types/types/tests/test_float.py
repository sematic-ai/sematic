# Third-party
import pytest

# Sematic
from sematic.types.casting import can_cast_type, safe_cast
from sematic.types.serialization import type_from_json_encodable, type_to_json_encodable


@pytest.mark.parametrize(
    "value, expected_cast_value, expected_err_msg",
    (
        (1.23, 1.23, None),
        (int(1), 1.0, None),
        ("3.14", 3.14, None),
        ("abc", None, "Cannot cast 'abc' to <class 'float'>"),
    ),
)
def test_safe_cast(value, expected_cast_value, expected_err_msg):
    cast_value, err_msg = safe_cast(value, float)
    assert cast_value == expected_cast_value
    if expected_err_msg is None:
        assert isinstance(cast_value, float)
    assert err_msg == expected_err_msg


def test_can_cast_type():
    assert can_cast_type(int, float) == (True, None)


def test_type_to_json_encodable():
    assert type_to_json_encodable(float) == {
        "type": ("builtin", "float", {}),
        "registry": {"float": []},
    }


def test_type_from_json_encodable():
    json_encodable = type_to_json_encodable(float)
    assert type_from_json_encodable(json_encodable) is float
