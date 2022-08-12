# Standard Library
import numbers
import typing

# Sematic
from sematic.types.registry import register_can_cast, register_to_json_encodable_summary
from sematic.types.serialization import value_to_json_encodable


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


@register_to_json_encodable_summary(float)
def _float_summary(value: float, _) -> float:
    return value_to_json_encodable(value, float)
