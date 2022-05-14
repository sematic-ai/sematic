"""
typing logic for the `int` type.
"""
# Standard library
import numbers
import typing

# Glow
from glow.types.registry import (
    register_can_cast,
    register_safe_cast,
    register_to_binary,
    register_from_binary,
)
from glow.types.serialization import to_binary_json, from_binary_json


@register_can_cast(int)
def can_cast_type(type_: type, _) -> typing.Tuple[bool, typing.Optional[str]]:
    """
    Type casting logic for `int`.

    Only subclasses of `numbers.Real` can cast to `int`.
    """
    if issubclass(type_, numbers.Real):
        return True, None

    return False, "Cannot cast {} to int".format(type_)


@register_safe_cast(int)
def safe_cast(value: typing.Any, _) -> typing.Tuple[typing.Any, typing.Optional[str]]:
    """
    Value casting logic for `int`.

    The native Python logic is preserved.
    """
    try:
        return int(value), None
    except ValueError as exception:
        return None, str(exception)


# hashlib.sha1(json.dumps(1).encode('utf-8')).hexdigest()


@register_to_binary(int)
def int_to_binary(value: int, _) -> bytes:
    return to_binary_json(value)


@register_from_binary(int)
def int_from_binary(binary: bytes, _) -> int:
    value = from_binary_json(binary)
    value = typing.cast(int, value)
    return value
