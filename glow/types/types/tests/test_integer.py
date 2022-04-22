# Standard library
import pytest

# Glow
from glow.types.types.float import Float
from glow.types.types.integer import Integer


@pytest.mark.parametrize(
    "value, expected_value",
    (
        (1, 1),
        ("1", 1),
        (1.23, 1),
    ),
)
def test_instantiation(value, expected_value):
    i = Integer(value)
    assert i == expected_value
    assert isinstance(i, Integer)


@pytest.mark.parametrize(
    "value, expected_cast_value, expected_err_msg",
    (
        (1, Integer(1), None),
        (1.23, Integer(1), None),
        ("42", Integer(42), None),
        ("abc", None, "invalid literal for int() with base 10: 'abc'"),
    ),
)
def test_can_cast(value, expected_cast_value, expected_err_msg):
    cast_value, err_msg = Integer.safe_cast(value)
    assert cast_value == expected_cast_value
    if expected_err_msg is None:
        assert isinstance(cast_value, Integer)
    assert err_msg == expected_err_msg


# Here we test that our ops overrides don't mess with the core logic


def test_add_int():
    value = Integer(1) + 1
    assert value == 2
    assert isinstance(value, int)


def test_add_float():
    value = Integer(1) + 1.5
    assert value == 2.5
    assert isinstance(value, float)


def test_sub_int():
    value = Integer(2) - 1
    assert value == 1
    assert isinstance(value, int)


def test_sub_float():
    value = Integer(2) - 1.5
    assert value == 0.5
    assert isinstance(value, float)


def test_multiply_int():
    value = Integer(1) * 2
    assert value == 2
    assert isinstance(value, int)


def test_multiply_float():
    value = Integer(1) * 2.5
    assert value == 2.5
    assert isinstance(value, float)


def test_truediv_int():
    value = Integer(4) / 3
    assert value == 1
    assert isinstance(value, int)


def test_truediv_float():
    value = Integer(3) / 2.0
    assert value == 1.5
    assert isinstance(value, float)
