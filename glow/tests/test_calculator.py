import pytest

from glow.calculator import Calculator, calculator
from glow.future import Future


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
        Calculator("abc")


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
        match=(
            "Variadic arguments are not supported."
            " glow.tests.test_calculator.func has variadic argument 'abc'"
        ),
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
