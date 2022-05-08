# Standard library
import numbers
import typing

# Glow
from glow.types.registry import register_can_cast, register_safe_cast


@register_can_cast(float)
def can_cast_type(type_: type) -> typing.Tuple[bool, typing.Optional[str]]:
    if issubclass(type_, numbers.Real):
        return True, None

    return False, "Cannot cast {} to float".format(type_)


@register_safe_cast(float)
def safe_cast(value: typing.Any) -> typing.Tuple[typing.Any, typing.Optional[str]]:
    try:
        return float(value), None
    except ValueError as exception:
        return None, str(exception)
