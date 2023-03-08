# Standard Library
import json
from typing import Any, Dict, List, Literal, Mapping, Optional, Tuple, Type, get_args

# Sematic
from sematic.types.casting import safe_cast
from sematic.types.registry import (
    SummaryOutput,
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
from sematic.utils.hashing import get_str_sha1_digest


@register_safe_cast(dict)
def _dict_safe_cast(value: Dict, type_: Type) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Casting logic for dictionaries.
    """
    if not isinstance(value, Mapping):
        return None, "{} is not a mapping. Cannot cast to {}.".format(
            repr(value), type_
        )

    type_args = get_args(type_)
    if type_args is None or type_args == ():
        return None, (
            "Dictionary doesn't have key/value types specified. Please use "
            "'Dict[KType, VType]' instead of 'Dict' or 'dict'. Dict[object, object] "
            "can be used for arbitrary dictionaries."
        )
    key_type, element_type = type_args

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
    # not using the values of the keys directly because the '<' operation is not
    # guaranteed to be implemented for all types, but the hash is guaranteed to be
    # implemented, since the keys must be hashable in order to be used as keys
    sorted_keys = sorted(value.keys(), key=hash)

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
def _dict_to_json_encodable_summary(value: Dict, type_: Type) -> SummaryOutput:
    """
    UI summary for dict

    TODO: Introduce a payload size limit like on List
    """
    key_type, element_type = type_.__args__

    blobs = {}
    unsorted_summaries = {}

    for key, value_ in value.items():
        key_summary, key_blobs = get_json_encodable_summary(key, key_type)
        value_summary, value_blobs = get_json_encodable_summary(value_, element_type)

        blobs.update(value_blobs)
        blobs.update(key_blobs)

        # Sorting keys for determinism
        # not using the values of the keys directly because the '<' operation is not
        # guaranteed to be implemented for all types.
        # Using sha1 of serialization
        hashed_key = get_str_sha1_digest(json.dumps(key_summary, sort_keys=True))
        unsorted_summaries[hashed_key] = (key_summary, value_summary)

    summary = [unsorted_summaries[key] for key in sorted(unsorted_summaries.keys())]

    return summary, blobs
