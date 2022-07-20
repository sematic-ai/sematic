# Standard library
import json
import math
import typing

# Sematic
from sematic.types.registry import (
    register_from_json_encodable,
    register_safe_cast,
    register_can_cast,
    register_to_json_encodable,
    register_to_json_encodable_summary,
)
from sematic.types.casting import safe_cast, can_cast_type
from sematic.types.serialization import (
    get_json_encodable_summary,
    value_from_json_encodable,
    value_to_json_encodable,
)


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

    element_char_len = None
    if len(complete_summary) > 0:
        element_char_len = len(json.dumps(complete_summary[0]))

    estimated_total_char_len = (
        (0 if element_char_len is None else len(value) * element_char_len)
        + 2
        + 2 * len(value)
    )

    max_item = math.floor((1000 / estimated_total_char_len))

    return {
        "length": len(value),
        "summary": complete_summary[:max_item],
    }
