"""
typing logic for the `int` type.
"""
# Standard library
import inspect
import numbers
import typing

# Sematic
from sematic.types.registry import register_can_cast, register_to_json_encodable_summary
from sematic.types.serialization import value_to_json_encodable


@register_can_cast(int)
def can_cast_type(type_: type, _) -> typing.Tuple[bool, typing.Optional[str]]:
    """
    Type casting logic for `int`.

    Only subclasses of `numbers.Real` can cast to `int`.
    """
    if inspect.isclass(type_) and issubclass(type_, numbers.Real):
        return True, None

    return False, "Cannot cast {} to int".format(type_)


@register_to_json_encodable_summary(int)
def _int_summary(value: int, _) -> int:
    return value_to_json_encodable(value, int)
