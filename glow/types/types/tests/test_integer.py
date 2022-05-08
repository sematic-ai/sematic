# Standard library
import pytest

# Glow
from glow.types.casting import safe_cast, can_cast_type


@pytest.mark.parametrize(
    "value, expected_cast_value, expected_err_msg",
    (
        (1, 1, None),
        (1.23, 1, None),
        ("42", 42, None),
        ("abc", None, "invalid literal for int() with base 10: 'abc'"),
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
