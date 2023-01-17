# Standard Library
from typing import Any, List, Tuple, Type, Union

try:
    # Python 3.9
    # Standard Library
    from types import GenericAlias  # type: ignore
except ImportError:
    # Python 3.8
    from typing import _GenericAlias as GenericAlias  # type: ignore

# Sematic
from sematic.abstract_future import AbstractFuture


def make_list_type(list_: List[Any]) -> Type[List]:
    """
    Attempts to make a List generic type representing the provided list.
    """
    if len(list_) == 0:
        return List[Any]

    element_type = None

    for item in list_:
        item_type = (
            item.calculator.output_type
            if isinstance(item, AbstractFuture)
            else type(item)
        )
        if element_type is None:
            element_type = item_type
        elif element_type != item_type:
            element_type = Union[element_type, item_type]

    return List[element_type]  # type: ignore


def make_tuple_type(tuple_: Tuple) -> GenericAlias:
    """
    Attempts to make a Tuple generic type representing the provided tuple.
    """
    element_types = [
        item.calculator.output_type if isinstance(item, AbstractFuture) else type(item)
        for item in tuple_
    ]

    return GenericAlias(tuple, tuple(element_types))
