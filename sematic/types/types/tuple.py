# Standard Library
from typing import Any, Iterable, List, Optional, Tuple, Type

# Sematic
from sematic.types.casting import safe_cast
from sematic.types.registry import (
    register_safe_cast,
    register_to_json_encodable,
    register_to_json_encodable_summary,
)
from sematic.types.serialization import (
    get_json_encodable_summary,
    value_to_json_encodable,
)


@register_safe_cast(tuple)
def _tuple_safe_cast(
    value: Tuple, type_: Type
) -> Tuple[Optional[Tuple], Optional[str]]:
    """
    Casting logic for tuples.

    Ellipsis not supported at this time.
    """
    if not isinstance(value, Iterable):
        return None, "{} not an iterable".format(value)

    element_types = type_.__args__

    if element_types[-1] is ...:
        return None, "Sematic does not support Ellipsis in Tuples yet (...)"

    if len(value) != len(element_types):
        return None, "Expected {} elements, got {}: {}".format(
            len(element_types), len(value), repr(value)
        )

    result: List[Any] = []  # type: ignore

    for element, element_type in zip(value, element_types):
        cast_element, error = safe_cast(element, element_type)
        if error is not None:
            return None, "Cannot cast {} to {}: {}".format(repr(value), type_, error)

        result.append(cast_element)

    return tuple(result), None


@register_to_json_encodable(tuple)
def _tuple_to_json_encodable(value: Tuple, type_: Type) -> List:
    """
    Serialization of tuples
    """
    return [
        value_to_json_encodable(element, element_type)
        for element, element_type in zip(value, type_.__args__)
    ]


@register_to_json_encodable_summary(tuple)
def _tuple_to_json_encodable_summary(value: Tuple, type_: Type) -> List:
    """
    Generate summary for the UI.
    """
    return [
        get_json_encodable_summary(element, element_type)
        for element, element_type in zip(value, type_.__args__)
    ]
