# Standard Library
from typing import Any, Optional, Tuple, Union

# Sematic
from sematic.types.casting import can_cast_type, safe_cast
from sematic.types.registry import (
    register_can_cast,
    register_safe_cast,
    register_to_json_encodable,
    register_to_json_encodable_summary,
)
from sematic.types.serialization import (
    get_json_encodable_summary,
    value_to_json_encodable,
)


@register_safe_cast(Union)
def _union_safe_cast(value: Any, type_: Any) -> Tuple[Any, Optional[str]]:
    unioned_types = type_.__args__

    # First we look for the identical type
    for unioned_type in unioned_types:
        if type_ is unioned_type:
            return value, None

    # If no match we look for one that casts
    for unioned_type in unioned_types:
        cast_value, error = safe_cast(value, unioned_type)
        if error is None:
            # Multiple types could match, we return the cast_value of the first found one
            # Ideally casting does not change value anyway
            return cast_value, None

    return None, "{} does not match any of {}".format(repr(value), unioned_types)


@register_can_cast(Union)
def _union_can_cast(from_type: Any, to_type: Any) -> Tuple[bool, Optional[str]]:
    unioned_types = to_type.__args__

    for unioned_type in unioned_types:
        can_cast, _ = can_cast_type(from_type, unioned_type)
        if can_cast:
            return True, None

    return False, "{} cannot cast to any of {}".format(from_type, unioned_types)


@register_to_json_encodable(Union)
def _union_to_json_encodable(value: Any, type_: Any) -> Any:
    # We assume that casting has already vetted type_

    return value_to_json_encodable(value, _get_value_type(value, type_))


@register_to_json_encodable_summary(Union)
def _union_to_summary(value: Any, type_: Any) -> Any:
    return get_json_encodable_summary(value, _get_value_type(value, type_))


def _get_value_type(value: Any, type_: Any) -> Any:
    for unioned_type in type_.__args__:
        _, error = safe_cast(value, unioned_type)
        if error is None:
            return unioned_type

    return type(value)
