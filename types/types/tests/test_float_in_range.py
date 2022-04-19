import pytest

from glow.types.generic_type import GenericMeta
from glow.types.types.float_in_range import FloatInRange


@pytest.mark.parametrize(
    "type_, parameters, name",
    (
        (
            FloatInRange[0, 1],
            dict(
                lower_bound=0, upper_bound=1, lower_inclusive=True, upper_inclusive=True
            ),
            "FloatInRange[0.0, 1.0, True, True]",
        ),
        (
            FloatInRange[0.4, 1.3, False, True],
            dict(
                lower_bound=0.4,
                upper_bound=1.3,
                lower_inclusive=False,
                upper_inclusive=True,
            ),
            "FloatInRange[0.4, 1.3, False, True]",
        ),
    ),
)
def test_parametrization(type_, parameters, name):
    assert issubclass(type_, FloatInRange)
    assert type_.get_parameters() == parameters
    assert type_.__name__ == name


@pytest.mark.parametrize(
    "type_, value, expected_cast_value, expected_error_msg",
    (
        (FloatInRange[0, 1], -1, None, "-1.0 is not in range [0.0, 1.0]"),
        (FloatInRange[0, 1], 0.4, 0.4, None),
        (FloatInRange[0, 1], 0.0, 0.0, None),
        (FloatInRange[0, 1], 1.0, 1.0, None),
        (FloatInRange[0, 1, False, True], 0, None, "0.0 is not in range (0.0, 1.0]"),
        (FloatInRange[0, 1, False, False], 1.0, None, "1.0 is not in range (0.0, 1.0)"),
    ),
)
def test_safe_cast(type_: GenericMeta, value, expected_cast_value, expected_error_msg):
    cast_value, error_msg = type_.safe_cast(value)
    assert cast_value == expected_cast_value

    if error_msg is None:
        assert isinstance(cast_value, type_)

    assert error_msg == expected_error_msg
