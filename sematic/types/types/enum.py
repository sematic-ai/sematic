# Standard Library
import typing
from enum import Enum

# Sematic
from sematic.types.registry import (
    register_can_cast,
    register_from_json_encodable,
    register_to_json_encodable,
    register_to_json_encodable_summary,
)


@register_can_cast(Enum)
def can_cast_type(
    from_type: typing.Type[Enum], to_type: typing.Type[Enum]
) -> typing.Tuple[bool, typing.Optional[str]]:
    """
    Type casting logic for `Enum`.

    The types must be equal
    """
    if from_type is to_type:
        return True, None

    return False, "{} does not match {}".format(from_type, to_type)


# Default safe_cast behavior is sufficient


@register_to_json_encodable_summary(Enum)
def _enum_summary(value: Enum, _) -> str:
    return _enum_to_encodable(value, _)


@register_to_json_encodable(Enum)
def _enum_to_encodable(value: Enum, type_: typing.Type[Enum]) -> str:
    # Ex: foo.bar.Color.RED
    if not isinstance(value, type_):
        raise ValueError(f"The value '{value}' is not a {type_.__name__}")
    return value.name


@register_from_json_encodable(Enum)
def _enum_from_encodable(value: str, type_: typing.Type[Enum]):
    value_name = value.split(".")[-1]
    if not hasattr(type_, value_name):
        raise ValueError(f"The type {type_.__name__} has no value '{value_name}'")
    deserialized = type_[value_name]
    return deserialized
