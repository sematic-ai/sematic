# Standard library
import numbers
import typing

# Glow
from glow.types.registry import register_can_cast
from glow.types.serialization import serializes_to_json


@register_can_cast(float)
def can_cast_type(type_: type, _) -> typing.Tuple[bool, typing.Optional[str]]:
    """
    Type casting logic for `float`.

    Only subclasses of `numbers.Real` can cast to `float`.
    """
    if issubclass(type_, numbers.Real):
        return True, None

    return False, "Cannot cast {} to float".format(type_)


# Default safe_cast behavior is sufficient


serializes_to_json(float)
