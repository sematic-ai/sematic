# Standard Library
from typing import Any, Dict, List, Literal, Mapping, Optional, Tuple, Type, get_args

# Sematic
from sematic.types.casting import safe_cast
from sematic.types.registry import (
    register_from_json_encodable,
    register_safe_cast,
    register_to_json_encodable,
    register_to_json_encodable_summary,
)
from sematic.types.serialization import (
    get_json_encodable_summary,
    value_from_json_encodable,
    value_to_json_encodable,
)


@register_safe_cast(dict)
def _dict_safe_cast(value: Dict, type_: Type) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Casting logic for dictionaries.
    """
    if not isinstance(value, Mapping):
        return None, "{} is not a mapping. Cannot cast to {}.".format(
            repr(value), type_
        )

    key_type, element_type = get_args(type_)

    cast_value = dict()

    for key, element in value.items():
        cast_key, error = safe_cast(key, key_type)
        if error is not None:
            return None, "Cannot cast {} to key type: {}".format(repr(key), error)

        cast_element, error = safe_cast(element, element_type)

        if error is not None:
            return None, "Cannot cast {} to value type: {}".format(repr(element), error)

        cast_value[cast_key] = cast_element

    return cast_value, None


@register_to_json_encodable(dict)
def _dict_to_json_encodable(
    value: Dict, type_: Type
) -> Dict[Literal["items"], List[Tuple[Any, Any]]]:
    """
    Dict serialization
    """
    key_type, element_type = type_.__args__

    # Sorting keys for determinism
    sorted_keys = sorted(value.keys())

    return {
        "items": [
            (
                value_to_json_encodable(key, key_type),
                value_to_json_encodable(value[key], element_type),
            )
            for key in sorted_keys
        ]
    }


@register_from_json_encodable(dict)
def _dict_from_json_encodable(
    value: Dict[str, List[Tuple[Any, Any]]], type_: Type
) -> Dict[Any, Any]:
    """
    Dict deserialization
    """
    key_type, element_type = get_args(type_)
    items = value["items"]

    return {
        value_from_json_encodable(key, key_type): value_from_json_encodable(
            element, element_type
        )
        for key, element in items
    }


@register_to_json_encodable_summary(dict)
def _dict_to_json_encodable_summary(value: Dict, type_: Type) -> List[Tuple[Any, Any]]:
    """
    UI summary for dict

    TODO: Introduce a payload size limit like on List
    """
    key_type, element_type = type_.__args__

    # Sorting keys for determinism
    sorted_keys = sorted(value.keys())

    return [
        (
            get_json_encodable_summary(key, key_type),
            get_json_encodable_summary(value[key], element_type),
        )
        for key in sorted_keys
    ]
