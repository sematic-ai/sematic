"""
Defining these operators in seperate modules in order to avoid circular
dependencies between Future and Calculator
"""
# Standard Library
# standard library
from typing import get_args, get_origin

# Sematic
from sematic.future import Future
from sematic.future_operators.getitem import __getitem__


def __iter__(self: Future):
    """
    Implementation of __iter__ on Futures.

    When users try to iterate on a future returning an iterable, a list of
    futures needs to be returned.

    Only supporting tuples for now.
    """
    is_tuple_future = False
    future_type = self.calculator.output_type

    is_tuple_future = get_origin(future_type) is tuple

    if not is_tuple_future:
        raise NotImplementedError(
            "Future.__iter__ is only supported on Tuple futures. Find a workaround at https://docs.sematic.dev/diving-deeper/future-algebra#unpacking-and-iteration"  # noqa: E501
        )

    yield from [__getitem__(self, idx) for idx, _ in enumerate(get_args(future_type))]


Future.__iter__ = __iter__  # type: ignore
