# standard library
from types import GenericAlias
from typing import cast

# Sematic
from sematic.future import Future
from sematic.future_operators.getitem import __getitem__


def __iter__(self: Future):
    is_tuple_future = False
    future_type: GenericAlias = cast(GenericAlias, self.calculator.output_type)

    try:
        is_tuple_future = future_type.__origin__ is tuple
    except AttributeError:
        pass

    if not is_tuple_future:
        raise NotImplementedError(
            "Future.__iter__ is only supported on Tuple futures. Find a workaround at https://docs.sematic.ai/diving-deeper/future-algebra#unpacking-and-iteration"  # noqa: E501
        )

    yield from [__getitem__(self, idx) for idx, _ in enumerate(future_type.__args__)]


Future.__iter__ = __iter__  # type: ignore
