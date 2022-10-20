# Standard Library
import json
import typing

# Sematic
from sematic.types.casting import can_cast_type, safe_cast
from sematic.types.registry import (
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


# Using `list` instead of `typing.List` here because
# `typing.List[T].__origin__` is `list`
@register_safe_cast(list)
def safe_cast_list(
    value: typing.Any, type_: typing.Any
) -> typing.Tuple[typing.Any, typing.Optional[str]]:
    """
    Value casting logic for `List[T]`.

    All list elements are attempted to cast to `T`.
    """
    if not isinstance(value, typing.Iterable):
        return None, "{} not an iterable".format(value)

    element_type = type_.__args__[0]

    result: typing.List[element_type] = []  # type: ignore

    for index, element in enumerate(value):
        cast_element, error = safe_cast(element, element_type)
        if error is not None:
            return None, "Cannot cast {} to {}: {}".format(value, type_, error)

        result.append(cast_element)

    return result, None


# Using `list` instead of `typing.List` here because
# `typing.List[T].__origin__` is `list`
@register_can_cast(list)
def can_cast_to_list(from_type: typing.Any, to_type: typing.Any):
    """
    Type casting logic for `List[T]`.

    `from_type` and `to_type` should be subscripted generics
    of the form `List[T]`.

    All subclasses of `Iterable` are castable to `List`: `List`, `Tuple`, `Dict`, `Set`.

    A type of the form `Iterable[A, B, C]` is castable to `List[T]` if all
    `A`, `B`, and `C` are castable to `T`.

    For example `Tuple[int, float]` is castable to `List[int]`, but `Tuple[int, str]`
    is not.
    """
    err_prefix = "Can't cast {} to {}:".format(from_type, to_type)

    if not isinstance(from_type, typing._GenericAlias):  # type: ignore
        return False, "{} not a subscripted generic".format(err_prefix)

    if not (
        isinstance(from_type.__origin__, type)
        and issubclass(from_type.__origin__, typing.Iterable)
    ):
        return False, "{} not an iterable".format(err_prefix)

    from_type_args = from_type.__args__

    element_type = to_type.__args__[0]

    for from_element_type in from_type_args:
        can_cast, error = can_cast_type(from_element_type, element_type)
        if can_cast is False:
            return False, "{}: {}".format(err_prefix, error)

    return True, None


@register_to_json_encodable(list)
def list_to_json_encodable(value: list, type_: typing.Any) -> list:
    element_type = type_.__args__[0]
    return [value_to_json_encodable(item, element_type) for item in value]


@register_from_json_encodable(list)
def list_from_json_encodable(value: list, type_: typing.Any) -> list:
    element_type = type_.__args__[0]
    return [value_from_json_encodable(item, element_type) for item in value]


@register_to_json_encodable_summary(list)
def list_to_json_encodable_summary(
    value: list, type_: typing.Any
) -> typing.Dict[str, typing.Any]:
    element_type = type_.__args__[0]

    complete_summary = [
        get_json_encodable_summary(item, element_type) for item in value
    ]

    max_item = 0
    if len(complete_summary) > 0:
        # this logic doesn't account for the "length" and "summary"
        # keys or outer wrapping brackets, but those represent roughly
        # 1 thousandth of the payload in the max case, and thus can
        # be ignored
        max_element_byte_len = max(
            len(json.dumps(element).encode("utf8")) for element in complete_summary
        )
        max_element_byte_len += 2  # for the comma and space between elements
        max_elements = int(MAX_SUMMARY_BYTES / max_element_byte_len)
        max_item = max(
            max_elements, 1
        )  # ensure there's always at least 1 element for non-empty lists

    return {
        "length": len(value),
        "summary": complete_summary[:max_item],
    }
