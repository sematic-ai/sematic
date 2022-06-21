# Standard library
from typing import List, Union

# Third-party
import pytest

# Sematic
from sematic.calculator import Calculator, calculator, _make_list, _convert_lists
from sematic.future import Future
from sematic.db.tests.fixtures import test_db  # noqa: F401
from sematic.api.tests.fixtures import mock_requests, test_client  # noqa: F401


def test_decorator_no_params():
    @calculator
    def func():
        pass

    assert isinstance(func, Calculator)


def test_decorator_with_params():
    @calculator()
    def func():
        pass

    assert isinstance(func, Calculator)


def test_doc():
    @calculator
    def func():
        """Some documentation"""
        pass

    assert func.__doc__ == "Some documentation"


def test_name():
    @calculator
    def abc():
        pass

    assert abc.__name__ == "abc"


def test_not_a_function():
    with pytest.raises(ValueError, match="not a function"):
        Calculator("abc", {}, None)


def test_types_not_specified():
    @calculator
    def func():
        pass

    assert func.input_types == dict()
    assert func.output_type is type(None)  # noqa: E721


def test_none_types():
    @calculator
    def func(a: None) -> None:
        pass

    assert func.output_type is type(None)  # noqa: E721
    assert func.input_types == dict(a=type(None))


def test_types_specified():
    @calculator
    def func(a: float) -> int:
        pass

    assert func.input_types == dict(a=float)
    assert func.output_type is int


def test_variadic():
    with pytest.raises(
        ValueError,
        match=("Variadic arguments are not supported."),
    ):

        @calculator
        def func(*abc):
            pass


def test_missing_types():
    with pytest.raises(
        ValueError,
        match=(
            "Missing calculator type annotations."
            " The following arguments are not annotated: 'a', 'b'"
        ),
    ):

        @calculator
        def func(a, b, c: float):
            pass


def test_call_fail_cast():
    @calculator
    def func(a: float) -> float:
        return a

    with pytest.raises(TypeError, match="Cannot cast 'abc' to <class 'float'>"):
        func("abc")


def test_call_pass_cast():
    @calculator
    def func(a: float) -> float:
        return a

    f = func(1.23)

    assert isinstance(f, Future)
    assert f.calculator is func
    assert set(f.kwargs) == {"a"}
    assert isinstance(f.kwargs["a"], float)
    assert f.kwargs["a"] == 1.23


def test_call_fail_binding():
    @calculator
    def func(a: float) -> float:
        return a

    with pytest.raises(TypeError, match="too many positional arguments"):
        func(1, 2)


@calculator
def foo() -> str:
    return "foo"


@calculator
def bar() -> str:
    return "bar"


def test_make_list():
    future = _make_list(List[str], [foo(), bar()])

    assert isinstance(future, Future)
    assert future.calculator.output_type is List[str]
    assert len(future.calculator.input_types) == 2


@calculator
def pipeline() -> List[str]:
    return _make_list(List[str], [foo(), bar(), "baz"])


def test_pipeline(test_db, mock_requests):  # noqa: F811
    output = pipeline().resolve()
    assert output == ["foo", "bar", "baz"]


def test_convert_lists(test_db, mock_requests):  # noqa: F811
    result = _convert_lists([1, foo(), [2, bar()], 3, [4, [5, foo()]]])

    assert isinstance(result, Future)
    assert len(result.kwargs) == 5
    assert (
        result.calculator.output_type
        is List[
            Union[
                int, str, List[Union[int, str]], List[Union[int, List[Union[int, str]]]]
            ]
        ]
    )

    assert isinstance(result.kwargs["v1"], Future)
    assert isinstance(result.kwargs["v2"], Future)
    assert isinstance(result.kwargs["v2"].kwargs["v1"], Future)
    assert isinstance(result.kwargs["v4"].kwargs["v1"].kwargs["v1"], Future)

    assert result.resolve() == [1, "foo", [2, "bar"], 3, [4, [5, "foo"]]]
