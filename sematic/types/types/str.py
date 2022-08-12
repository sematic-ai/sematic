"""
Casting and serialization logic for `str`.
"""
# Standard Library
import inspect
import typing

# Sematic
from sematic.types.registry import (
    register_can_cast,
    register_safe_cast,
    register_to_json_encodable_summary,
)
from sematic.types.serialization import value_to_json_encodable


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
    if inspect.isclass(type_) and issubclass(type_, str):
        return True, None

    return False, "{} cannot cast to str".format(type_)


@register_to_json_encodable_summary(str, typing.Text)
def _str_summary(value: str, _) -> str:
    return value_to_json_encodable(value, str)
