# Standard Library
import typing
from enum import Enum

# Sematic
from sematic.types.registry import register_can_cast, register_to_json_encodable_summary


@register_can_cast(Enum)
def can_cast_type(
    from_type: typing.Type[Enum], to_type: typing.Type[Enum]
) -> typing.Tuple[bool, typing.Optional[str]]:
    """
    Type casting logic for `Enum`.

    The to_type must be a parent type of the from_type for castability
    """
    if issubclass(from_type, to_type):
        return True, None

    return False, "{} is not a child class of {}".format(from_type, to_type)


# Default safe_cast behavior is sufficient


@register_to_json_encodable_summary(Enum)
def _enum_summary(value: Enum, _) -> str:
    return value.name
