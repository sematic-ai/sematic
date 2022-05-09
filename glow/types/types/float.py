# Standard library
import numbers
import typing

# Glow
from glow.types.registry import register_can_cast, register_safe_cast


@register_can_cast(float)
def can_cast_type(type_: type, _) -> typing.Tuple[bool, typing.Optional[str]]:
    """
    Type casting logic for `float`.

    Only subclasses of `numbers.Real` can cast to `float`.
    """
    if issubclass(type_, numbers.Real):
        return True, None

    return False, "Cannot cast {} to float".format(type_)


@register_safe_cast(float)
def safe_cast(value: typing.Any, _) -> typing.Tuple[typing.Any, typing.Optional[str]]:
    """
    Value casting logic for `float`.

    The native Python logic is preserved.
    """
    try:
        return float(value), None
    except ValueError as exception:
        return None, str(exception)
