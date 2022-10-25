# Standard Library
from contextlib import contextmanager
from dataclasses import dataclass
from inspect import Signature
from typing import Callable, Dict, Iterator, List
from unittest import mock

# Sematic
from sematic.calculator import Calculator


@dataclass
class SematicFuncMock:
    """Object with info about a mocked Sematic func.

    Attributes
    ----------
    mock:
        A unittest.mock.MagicMock which corresponds to the underlying function before the
        @sematic.func decorator was applied to it
    original:
        The original (unmocked) underlying function before the @sematic.func decorator
        was applied to it
    signature:
        The signature of the Sematic func
    """

    mock: mock.MagicMock
    original: Callable
    signature: Signature


@contextmanager
def mock_sematic_funcs(
    funcs: List[Calculator],
) -> Iterator[Dict[Calculator, SematicFuncMock]]:
    """Mock Sematic funcs so they still return futures and check input/output types.

    To be used as a context manager:
    ```
        with mock_sematic_funcs(funcs=[pipeline_step_1, pipeline_step2]) as mocks:
            mocks[pipeline_step_1].mock.return_value = ...
            mocks[pipeline_step_2].mock.return_value = ...
            pipeline().resolve(sematic.SilentResolver())
    ```

    When a function decorated with @sematic.func is provided here, it will still
    behave as a Sematic func in that it will return a future, check input/output
    types and values during execution, and participate in helping Sematic construct
    a DAG. However, when it comes time to actually execute the code that was decorated,
    it is mocked out. This is thus useful for checking the structure of a Sematic
    pipeline or mocking out an individual Sematic func within one in case you don't want
    it to execute during testing.

    Parameters
    ----------
    funcs:
        a list of Sematic funcs you want to mock

    Returns
    -------
    Yields a dictionary mapping the Sematic func to an object with handles
    to the mocks.
    For every key in the dictionary, the following is available:
    - yielded[my_func].mock  # a MagicMock that will be used when it is actually
        time to execute the @sematic.func decorated code
    - yielded[my_func].original  # the original function that was
        decorated with @sematic.func
    """
    func_mocks = {}
    try:
        for func in funcs:
            func_mocks[func] = SematicFuncMock(
                mock=mock.MagicMock(),
                original=func._func,
                signature=func.__signature__(),
            )
            func._func = func_mocks[func].mock
            func._func.__signature__ = func_mocks[func].signature
        yield func_mocks
    finally:
        for func in funcs:
            if not isinstance(func, Calculator):
                raise ValueError(
                    f"mock_sematic_funcs(funcs=[...]) must be given a list of "
                    f"functions decorated with @sematic.func, but one of the "
                    f"elements was: {func}"
                )
            func._func = func_mocks[func].original  # type: ignore
