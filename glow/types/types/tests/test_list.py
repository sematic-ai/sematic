# Standard library
import typing

# Third-party
import pytest

# Glow
from glow.types.casting import safe_cast, can_cast_type


@pytest.mark.parametrize(
    "type_, value, expected_cast_value, expected_error",
    (
        (typing.List[int], [1, 2, 3], [1, 2, 3], None),
        (typing.List[int], [1.2, 3.4], [1, 3], None),
        (typing.List[float], ["1.2", 3], [1.2, 3], None),
        (
            typing.List[float],
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
        (typing.List[float], typing.List[int], True, None),
        # Need to implement str casting logic
        # (typing.List[float], typing.List[str], True, None),
        (
            float,
            typing.List[int],
            False,
            "Can't cast <class 'float'> to typing.List[int]: not a subscripted generic",
        ),
        (typing.Tuple[int, float], typing.List[float], True, None),
        (
            typing.Tuple[typing.List[float], typing.List[int]],
            typing.List[typing.List[int]],
            True,
            None,
        ),
    ),
)
def test_can_cast_type(from_type, to_type, expected_can_cast, expected_error):
    can_cast, error = can_cast_type(from_type, to_type)
    assert can_cast is expected_can_cast
    assert error == expected_error
