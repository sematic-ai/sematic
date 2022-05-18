"""
Casting and serialization logic for `str`.
"""
# Standard library
import typing

# Glow
from glow.types.registry import register_safe_cast, register_can_cast
from glow.types.serialization import serializes_to_json


@register_safe_cast(str, typing.Text)
def safe_cast_str(
    value: typing.Any, type_: typing.Type[str]
) -> typing.Tuple[typing.Optional[str], typing.Optional[str]]:
    """
    Value casting logic for `str`.
    Only instances of `str` and subclasses can cast to `str`.
    """
    if isinstance(value, str):
        return value, None

    return None, "Cannot cast {} to {}".format(repr(value), type_)


@register_can_cast(str, typing.Text)
def can_cast_to_str(type_: type, _) -> typing.Tuple[bool, typing.Optional[str]]:
    """
    Type casting logic for `str`.
    Only subclasses of `str` can cast to `str`.
    """
    if issubclass(type_, str):
        return True, None

    return False, "{} cannot cast to {}".format(type_, str)


serializes_to_json(str)
