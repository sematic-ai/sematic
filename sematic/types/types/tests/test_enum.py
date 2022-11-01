# Standard Library
from enum import Enum, unique

# Third-party
import pytest

# Sematic
from sematic.types.serialization import (
    value_from_json_encodable,
    value_to_json_encodable,
)
from sematic.types.types.enum import (
    _enum_from_encodable,
    _enum_to_encodable,
    can_cast_type,
)


class SomethingExotic:
    def __init__(self, number):
        self.number = number


@unique
class Color(Enum):
    RED = "RED"
    GREEN = "GREEN"
    BLUE = "BLUE"


@unique
class ExoticNumbers(Enum):
    MEANING_OF_LIFE = SomethingExotic(42)
    LUCKY_NUMBER = SomethingExotic(7)


def test_to_from_encodable():
    encoded = _enum_to_encodable(Color.RED, Color)
    assert encoded == "RED"

    # ensures registration worked
    assert encoded == value_to_json_encodable(Color.RED, Color)
    decoded = _enum_from_encodable(encoded, Color)
    assert decoded == value_from_json_encodable(encoded, Color)
    assert decoded == Color.RED

    encoded = _enum_to_encodable(ExoticNumbers.LUCKY_NUMBER, ExoticNumbers)
    assert encoded == "LUCKY_NUMBER"
    decoded = _enum_from_encodable(encoded, ExoticNumbers)
    assert decoded == ExoticNumbers.LUCKY_NUMBER
    assert decoded.value.number == 7

    with pytest.raises(
        ValueError, match=r"The value 'ExoticNumbers.LUCKY_NUMBER' is not a Color"
    ):
        _enum_to_encodable(ExoticNumbers.LUCKY_NUMBER, Color)

    with pytest.raises(ValueError, match=r"The type Color has no value 'LUCKY_NUMBER'"):
        _enum_from_encodable("LUCKY_NUMBER", Color)


def test_can_cast_type():
    assert can_cast_type(Color, Color) == (True, None)
    assert can_cast_type(Color, SomethingExotic) == (
        False,
        "<enum 'Color'> does not match "
        "<class 'sematic.types.types.tests.test_enum.SomethingExotic'>",
    )
