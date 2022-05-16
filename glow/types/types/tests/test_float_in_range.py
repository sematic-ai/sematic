# Third party
import pytest

# Glow
from glow.types.casting import can_cast_type, safe_cast
from glow.types.generic_type import GenericMeta
from glow.types.serialization import to_binary
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
    "type_lambda, expected_err",
    (
        (lambda: FloatInRange[0], "Not enough arguments"),
        (lambda: FloatInRange[0, 1, 2, 3, 4], "Too many arguments"),
        (lambda: FloatInRange["a", 1], "lower_bound must be a number"),
        (lambda: FloatInRange[0, "b"], "upper_bound must be a number"),
        (lambda: FloatInRange[1, 0], "lower bound 1.0 should be <= to upper bound 0.0"),
        (lambda: FloatInRange[0, 1, "a"], "lower_inclusive should be a boolean"),
        (lambda: FloatInRange[0, 1, True, "a"], "upper_inclusive should be a boolean"),
    ),
)
def test_parametrize(type_lambda, expected_err):
    with pytest.raises(ValueError, match=expected_err):
        type_lambda()


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
    cast_value, error_msg = safe_cast(value, type_)
    assert cast_value == expected_cast_value

    if error_msg is None:
        assert isinstance(cast_value, type_)

    assert error_msg == expected_error_msg


def test_add():
    FloatIn01 = FloatInRange[0, 1]
    a = FloatIn01(0.3)
    assert isinstance(a, FloatIn01)
    b = a + 2
    assert isinstance(b, float)
    assert not isinstance(b, FloatIn01)


def test_multiply():
    FloatIn01 = FloatInRange[0, 1]
    a = FloatIn01(0.3)
    assert isinstance(a, FloatIn01)
    b = a * 2
    assert isinstance(b, float)
    assert not isinstance(b, FloatIn01)


@pytest.mark.parametrize(
    "type1, type2, expected_can_cast, expected_err",
    (
        (FloatInRange[0, 1], FloatInRange[0.1, 0.7], True, None),
        (FloatInRange[0, 1, True, True], FloatInRange[0, 1, True, True], True, None),
        (FloatInRange[0, 1, True, True], FloatInRange[0, 1, False, True], True, None),
        (FloatInRange[0, 1, True, True], FloatInRange[0, 1, True, False], True, None),
        (
            FloatInRange[0, 1],
            FloatInRange[-0.5, 1],
            False,
            (
                "Incompatible ranges:"
                " FloatInRange[-0.5, 1.0, True, True]'s lower bound"
                " is lower than FloatInRange[0.0, 1.0, True, True]'s"
            ),
        ),
        (
            FloatInRange[0, 1],
            FloatInRange[0, 1.5],
            False,
            (
                "Incompatible ranges:"
                " FloatInRange[0.0, 1.5, True, True]'s upper bound"
                " is greater than FloatInRange[0.0, 1.0, True, True]'s"
            ),
        ),
        (
            FloatInRange[0, 1, False, True],
            FloatInRange[0, 1, True, True],
            False,
            (
                "Incompatible ranges:"
                " FloatInRange[0.0, 1.0, False, True] has an exclusive"
                " lower bound, FloatInRange[0.0, 1.0, True, True] has"
                " an inclusive lower bound"
            ),
        ),
        (
            FloatInRange[0, 1, True, False],
            FloatInRange[0, 1, True, True],
            False,
            (
                "Incompatible ranges:"
                " FloatInRange[0.0, 1.0, True, False] has an exclusive"
                " upper bound, FloatInRange[0.0, 1.0, True, True] has"
                " an inclusive upper bound"
            ),
        ),
    ),
)
def test_can_cast_type(type1, type2, expected_can_cast, expected_err):
    can_cast, err = can_cast_type(type2, type1)
    assert can_cast == expected_can_cast
    assert err == expected_err


def test_to_binary():
    t = FloatInRange[0, 1]
    binary = to_binary(0.5, t)
    assert binary.decode("utf-8") == "0.5"
