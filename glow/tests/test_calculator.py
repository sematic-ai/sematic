import pytest

from glow.calculator import Calculator, calculator
from glow.future import Future
from glow.types.types.null import Null
from glow.types.types.float import Float


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
    assert func.output_type is Null


def test_input_type_not_type():
    class NotAType:
        pass

    with pytest.raises(
        ValueError, match="NotAType is not a valid type annotation for a"
    ):

        @calculator
        def func(a: NotAType):
            pass


def test_output_type_not_type():
    class NotAType:
        pass

    with pytest.raises(
        ValueError, match="NotAType is not a valid type annotation for return"
    ):

        @calculator
        def func() -> NotAType:
            pass


def test_types_specified():
    @calculator
    def func(a: Null) -> Float:
        pass

    assert func.input_types == dict(a=Null)
    assert func.output_type is Float


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
        def func(a, b, c: Float):
            pass


def test_call_fail_cast():
    @calculator
    def func(a: Float) -> Float:
        return a

    with pytest.raises(TypeError, match="could not convert string to float"):
        func("abc")


def test_call_pass_cast():
    @calculator
    def func(a: Float) -> Float:
        return a

    f = func(1.23)

    assert isinstance(f, Future)
    assert f.calculator is func
    assert set(f.kwargs) == {"a"}
    assert isinstance(f.kwargs["a"], Float)
    assert f.kwargs["a"] == 1.23


def test_call_fail_binding():
    @calculator
    def func(a: Float) -> Float:
        return a

    with pytest.raises(TypeError, match="too many positional arguments"):
        func(1, 2)
