"""
typing logic for the `int` type.
"""
# Standard library
import numbers
import typing

# Glow
from glow.types.registry import register_can_cast
from glow.types.serialization import serializes_to_json


@register_can_cast(int)
def can_cast_type(type_: type, _) -> typing.Tuple[bool, typing.Optional[str]]:
    """
    Type casting logic for `int`.

    Only subclasses of `numbers.Real` can cast to `int`.
    """
    if issubclass(type_, numbers.Real):
        return True, None

    return False, "Cannot cast {} to int".format(type_)


serializes_to_json(int)
