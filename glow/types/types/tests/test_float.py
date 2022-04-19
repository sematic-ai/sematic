import pytest

from glow.types.types.float import Float


@pytest.mark.parametrize(
    "value, expected_value",
    (
        (1.23, 1.23),
        ("3.14", 3.14),
        (int(1), 1.0),
    ),
)
def test_instantiation(value, expected_value):
    f = Float(value)
    assert f == expected_value
    assert isinstance(f, float)
    assert isinstance(f, Float)


@pytest.mark.parametrize(
    "value, expected_cast_value, expected_err_msg",
    (
        (1.23, Float(1.23), None),
        (int(1), Float(1.0), None),
        ("3.14", Float(3.14), None),
        ("abc", None, "could not convert string to float: 'abc'"),
    ),
)
def test_can_cast(value, expected_cast_value, expected_err_msg):
    cast_value, err_msg = Float.safe_cast(value)
    assert cast_value == expected_cast_value
    if expected_err_msg is None:
        assert isinstance(cast_value, Float)
    assert err_msg == expected_err_msg
