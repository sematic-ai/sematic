# Standard Library
import json
import typing

# Sematic
from sematic.types.casting import can_cast_type, safe_cast
from sematic.types.registry import (
    SummaryOutput,
    register_can_cast,
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


MAX_SUMMARY_BYTES = 2**17  # 128 kB


@register_safe_cast(set)
def _set_safe_cast(
    value: typing.Set, type_: typing.Type
) -> typing.Tuple[typing.Optional[typing.Set], typing.Optional[str]]:
    """
    Casting logic for `Set[T]`.

    All elements in set are attempted to cast to `T`.
    """
    if not isinstance(value, typing.Iterable):
        return None, f"{value} not an iterable"

    element_type = typing.get_args(type_)[0]

    result: typing.Set[element_type] = set()  # type: ignore

    for element in value:
        cast_element, error = safe_cast(element, element_type)
        if error:
            return None, f"Cannot cast {value} to {type_}: {error}"

        result.add(cast_element)

    return result, None


@register_to_json_encodable(set)
def _set_to_json_encodable(value: set, type_: typing.Any) -> typing.List:
    """
    Serialization of sets
    """
    element_type = typing.get_args(type_)[0]
    return [value_to_json_encodable(item, element_type) for item in value]


@register_from_json_encodable(set)
def _set_from_json_encodable(value: set, type_: typing.Any) -> typing.Set[typing.Any]:
    """
    Deserialize a sets
    """
    element_type = typing.get_args(type_)[0]
    return set(value_from_json_encodable(item, element_type) for item in value)


@register_can_cast(set)
def _can_cast_to_set(
    from_type: typing.Any, to_type: typing.Any
) -> typing.Tuple[bool, typing.Optional[str]]:
    """
    Type casting logic for `Set[T]`.

    `from_type` and `to_type` should be subscripted generics
    of the form `Set[T]`.

    All subclasses of `Iterable` are castable to `Set`: `List`, `Tuple`, `Dict`, `Set`.

    A type of the form `Iterable[A, B, C]` is castable to `Set[T]` if all
    `A`, `B`, and `C` are castable to `T`.

    For example `Tuple[int, float]` is castable to `Set[int]`, but `Tuple[int, str]`
    is not.
    """
    err_prefix = "Can't cast {} to {}:".format(from_type, to_type)

    if len(typing.get_args(from_type)) == 0:  # type: ignore
        return False, "{} not a subscripted generic".format(err_prefix)

    if not (
        isinstance(typing.get_origin(from_type), type)
        and issubclass(typing.get_origin(from_type), typing.Iterable)  # type: ignore
    ):
        return False, "{} not an iterable".format(err_prefix)

    from_type_args = typing.get_args(from_type)

    element_type = typing.get_args(to_type)[0]

    for from_element_type in from_type_args:
        can_cast, error = can_cast_type(from_element_type, element_type)
        if can_cast is False:
            return False, "{}: {}".format(err_prefix, error)

    return True, None


@register_to_json_encodable_summary(set)
def _set_to_json_encodable_summary(
    value: typing.Set, type_: typing.Type
) -> SummaryOutput:
    """
    Summary for the UI
    """
    complete_summary, blobs = [], []
    element_type = typing.get_args(type_)[0]

    for item in value:
        item_summary, item_blob = get_json_encodable_summary(item, element_type)
        complete_summary.append(item_summary)
        blobs.append(item_blob)

    max_item = 0
    if len(complete_summary) > 0:
        # this logic doesn't account for the "length" and "summary"
        # keys or outer wrapping brackets, but those represent roughly
        # 1 thousandth of the payload in the max case, and thus can
        # be ignored
        max_element_byte_len = max(
            len(json.dumps(element).encode("utf8")) for element in complete_summary
        )
        max_element_byte_len += 2
        max_elements = int(MAX_SUMMARY_BYTES / max_element_byte_len)
        max_item = max(
            max_elements, 1
        )  # ensure there's always at least 1 element for non-empty lists

    blobs_dict = {}
    for item_blobs in blobs[:max_item]:
        blobs_dict.update(item_blobs)

    return {
        "length": len(value),
        "summary": complete_summary[:max_item],
    }, blobs_dict
