# Standard library
import collections.abc
from typing import Any, Dict, List, Sequence, Type, TypeVar, Union

# Sematic
from sematic.abstract_future import AbstractFuture
from sematic.calculator import Calculator
from sematic.types.casting import can_cast_type, safe_cast
from sematic.types.registry import get_origin_type, is_valid_typing_alias


OutputType = TypeVar("OutputType")


def make_list(type_: Type[OutputType], list_with_futures: Sequence[Any]) -> OutputType:
    """
    Given a list with futures, returns a future List.
    """
    if not (is_valid_typing_alias(type_) and get_origin_type(type_) is list):
        raise Exception("type_ must be a List type.")

    if not isinstance(list_with_futures, collections.abc.Sequence):
        raise Exception("list_with_futures must be a collections.Sequence.")

    element_type = type_.__args__[0]  # type: ignore

    input_types = {}
    inputs = {}

    for i, item in enumerate(list_with_futures):
        if isinstance(item, AbstractFuture):
            can_cast, error = can_cast_type(item.calculator.output_type, element_type)
            if not can_cast:
                raise TypeError("Invalid value: {}".format(error))
        else:
            _, error = safe_cast(item, element_type)
            if error is not None:
                raise TypeError("Invalid value: {}".format(error))

        input_types["v{}".format(i)] = element_type
        inputs["v{}".format(i)] = item

    source_code = """
def _make_list({inputs}):
    return [{inputs}]
    """.format(
        inputs=", ".join("v{}".format(i) for i in range(len(list_with_futures)))
    )
    scope: Dict[str, Any] = {"__name__": __name__}
    exec(source_code, scope)
    _make_list = scope["_make_list"]

    return Calculator(_make_list, input_types=input_types, output_type=type_)(**inputs)


def convert_lists(value_):
    for idx, item in enumerate(value_):
        if isinstance(item, list):
            value_[idx] = convert_lists(item)

    if any(isinstance(item, AbstractFuture) for item in value_):
        output_type = None
        for item in value_:
            item_type = (
                item.calculator.output_type
                if isinstance(item, AbstractFuture)
                else type(item)
            )
            if output_type is None:
                output_type = item_type
            elif output_type != item_type:
                output_type = Union[output_type, item_type]

        return make_list(List[output_type], value_)

    return value_
