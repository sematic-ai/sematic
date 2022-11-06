# Standard Library
from typing import Any, List, Union

# Third-party
import pytest

# Sematic
from sematic.abstract_calculator import CalculatorError
from sematic.calculator import Calculator, _convert_lists, _make_list, func
from sematic.db.tests.fixtures import test_db  # noqa: F401
from sematic.future import Future
from sematic.resolvers.resource_requirements import (  # noqa: F401
    KubernetesResourceRequirements,
    ResourceRequirements,
)
from sematic.utils.exceptions import ResolutionError


def test_decorator_no_params():
    @func
    def f():
        pass

    assert isinstance(f, Calculator)


def test_decorator_with_params():
    @func()
    def f():
        pass

    assert isinstance(f, Calculator)


def test_any():
    expected = (
        r"Invalid type annotation for argument 'x' "
        r"of sematic.tests.test_calculator.f: 'Any' is "
        r"not a Sematic-supported type. Use 'object' instead."
    )
    with pytest.raises(TypeError, match=expected):

        @func
        def f1(x: Any) -> None:
            pass

    @func
    def f2(x: object) -> None:
        pass


def test_doc():
    @func
    def f():
        """Some documentation"""
        pass

    assert f.__doc__ == "Some documentation"


def test_name():
    @func
    def abc():
        pass

    assert abc.__name__ == "abc"


def test_not_a_function():
    with pytest.raises(ValueError, match="not a function"):
        Calculator("abc", {}, None)


def test_inline_and_resource_reqs():
    with pytest.raises(
        ValueError, match="Inline functions cannot have resource requirements"
    ):

        @func(
            inline=True,
            resource_requirements=ResourceRequirements(
                KubernetesResourceRequirements()
            ),
        )
        def abc():
            pass


def test_types_not_specified():
    @func
    def f():
        pass

    assert f.input_types == dict()
    assert f.output_type is type(None)  # noqa: E721


def test_none_types():
    @func
    def f(a: None) -> None:
        pass

    assert f.output_type is type(None)  # noqa: E721
    assert f.input_types == dict(a=type(None))


def test_types_specified():
    @func
    def f(a: float) -> int:
        pass

    assert f.input_types == dict(a=float)
    assert f.output_type is int


def test_variadic():
    with pytest.raises(
        ValueError,
        match=("Variadic arguments are not supported."),
    ):

        @func
        def f(*abc):
            pass


def test_missing_types():
    with pytest.raises(
        ValueError,
        match=(
            "Missing calculator type annotations."
            " The following arguments are not annotated: 'a', 'b'"
        ),
    ):

        @func
        def f(a, b, c: float):
            pass


def test_call_fail_cast():
    @func
    def f(a: float) -> float:
        return a

    with pytest.raises(TypeError, match="Cannot cast 'abc' to <class 'float'>"):
        f("abc")


def test_call_pass_cast():
    @func
    def f(a: float) -> float:
        return a

    ff = f(1.23)

    assert isinstance(ff, Future)
    assert ff.calculator is f
    assert set(ff.kwargs) == {"a"}
    assert isinstance(ff.kwargs["a"], float)
    assert ff.kwargs["a"] == 1.23


def test_call_fail_binding():
    @func
    def f(a: float) -> float:
        return a

    with pytest.raises(TypeError, match="too many positional arguments"):
        f(1, 2)


@func
def foo() -> str:
    return "foo"


@func
def bar() -> str:
    return "bar"


def test_make_list():
    future = _make_list(List[str], [foo(), bar()])

    assert isinstance(future, Future)
    assert future.calculator.output_type is List[str]
    assert len(future.calculator.input_types) == 2


@func
def pipeline() -> List[str]:
    return [foo(), bar(), "baz"]


def test_pipeline():
    output = pipeline().resolve(tracking=False)
    assert output == ["foo", "bar", "baz"]


def test_convert_lists():
    result = _convert_lists([1, foo(), [2, bar()], 3, [4, [5, foo()]]])

    assert isinstance(result, Future)
    assert result.props.inline is True
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

    @func
    def pipeline() -> List[
        Union[
            int,
            str,
            List[Union[int, str]],
            List[Union[int, List[Union[int, str]]]],
        ]
    ]:
        return [1, foo(), [2, bar()], 3, [4, [5, foo()]]]  # type: ignore

    assert pipeline().resolve(tracking=False) == [
        1,
        "foo",
        [2, "bar"],
        3,
        [4, [5, "foo"]],
    ]


def test_inline_default():
    @func
    def f():
        pass

    assert f._inline is True
    assert f().props.inline is True


def test_inline():
    @func(inline=False)
    def f():
        pass

    assert f._inline is False
    assert f().props.inline is False


def test_resource_requirements():
    resource_requirements = ResourceRequirements(
        kubernetes=KubernetesResourceRequirements(node_selector={"a": "b"}, requests={})
    )

    @func(resource_requirements=resource_requirements, inline=False)
    def f():
        pass

    assert f._resource_requirements == resource_requirements
    assert f().props.resource_requirements == resource_requirements


def test_resolve_error():
    @func()
    def f():
        raise ValueError("Intentional error")

    with pytest.raises(ResolutionError) as exc_info:
        # resolving should surface the ResolutionError,
        # with root cause as __context__
        # see https://peps.python.org/pep-0409/#language-details
        f().resolve(tracking=False)

    assert isinstance(exc_info.value.__context__, CalculatorError)
    assert isinstance(exc_info.value.__context__.__context__, ValueError)
    assert "Intentional error" in str(exc_info.value.__context__.__context__)


def test_calculate_error():
    @func()
    def f():
        raise ValueError("Intentional error")

    with pytest.raises(CalculatorError) as exc_info:
        # calling calculate should surface the CalculatorError,
        # with root cause as __context__
        # see https://peps.python.org/pep-0409/#language-details
        f.calculate()

    assert isinstance(exc_info.value.__context__, ValueError)
    assert "Intentional error" in str(exc_info.value.__context__)
