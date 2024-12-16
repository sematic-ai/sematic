# Standard Library
from typing import Any, List, Tuple, Union

# Third-party
import pytest

# Sematic
from sematic.abstract_function import FunctionError
from sematic.db.tests.fixtures import test_db  # noqa: F401
from sematic.function import (
    Function,
    _convert_lists,
    _convert_tuples,
    _make_list,
    _make_tuple,
    func,
)
from sematic.future import Future
from sematic.resolvers.resource_requirements import (  # noqa: F401
    KubernetesResourceRequirements,
    ResourceRequirements,
)
from sematic.runners.silent_runner import SilentRunner
from sematic.utils.exceptions import PipelineRunError


def test_decorator_no_params():
    @func
    def f():
        pass

    assert isinstance(f, Function)


def test_decorator_with_params():
    @func()
    def f():
        pass

    assert isinstance(f, Function)


def test_any():
    expected = (
        r"Invalid type annotation for argument 'x' "
        r"of sematic.tests.test_function.f1: 'Any' is "
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
    with pytest.raises(
        TypeError, match=r".*can only be used with functions. But 'abc' is a 'str'."
    ):
        Function("abc", {}, None)

    with pytest.raises(
        TypeError, match=r".*can only be used with functions, not methods.*"
    ):

        class SomeClass:
            @func
            def some_method(self: object) -> None:
                pass

    with pytest.raises(
        TypeError,
        match=r".*can't be used with async functions, generators, or coroutines.*",
    ):

        @func
        def a_generator() -> object:
            yield 42

    with pytest.raises(
        TypeError,
        match=r".*can't be used with async functions, generators, or coroutines.*",
    ):

        @func
        async def an_async_func() -> int:
            return 42


def test_inline_and_resource_reqs():
    with pytest.raises(
        ValueError, match="Only Standalone Functions can have resource requirements"
    ):

        @func(
            standalone=False,
            resource_requirements=ResourceRequirements(KubernetesResourceRequirements()),
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
        return int(a)

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
            "Missing function type annotations."
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
    assert ff.function is f
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


@func
def baz() -> int:
    return 42


def test_make_list():
    future = _make_list(List[str], [foo(), bar()])

    assert isinstance(future, Future)
    assert future.function.output_type is List[str]
    assert len(future.function.input_types) == 2


def test_make_tuple():
    future = _make_tuple(Tuple[str, int], (bar(), baz()))

    assert isinstance(future, Future)
    assert future.function.output_type is Tuple[str, int]
    assert len(future.function.input_types) == 2
    assert future.function.execute(v0="a", v1=42) == ("a", 42)


@func
def pipeline() -> List[str]:
    return [foo(), bar(), "baz"]


@func
def tuple_pipeline() -> Tuple[str, int, str]:
    return (foo(), baz(), "qux")


def test_pipeline():
    output = SilentRunner().run(pipeline())
    assert output == ["foo", "bar", "baz"]


def test_tuple_pipeline():
    output = SilentRunner().run(tuple_pipeline())
    assert output == ("foo", 42, "qux")


def test_convert_lists():
    result = _convert_lists([1, foo(), [2, bar()], 3, [4, [5, foo()]]])

    assert isinstance(result, Future)
    assert result.props.standalone is False
    assert len(result.kwargs) == 5
    assert (
        result.function.output_type
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
    def pipeline() -> (
        List[
            Union[
                int,
                str,
                List[Union[int, str]],
                List[Union[int, List[Union[int, str]]]],
            ]
        ]
    ):
        return [1, foo(), [2, bar()], 3, [4, [5, foo()]]]  # type: ignore

    assert SilentRunner().run(pipeline()) == [
        1,
        "foo",
        [2, "bar"],
        3,
        [4, [5, "foo"]],
    ]


def test_convert_tuples():
    value = (42, [1, baz(), 3], (foo(), bar()), foo())
    expected_type = Tuple[int, List[int], Tuple[str, str], str]
    result = _convert_tuples(value, expected_type)
    assert isinstance(result, Future)
    assert result.props.standalone is False

    @func
    def pipeline() -> expected_type:
        return value

    assert SilentRunner().run(pipeline()) == (42, [1, 42, 3], ("foo", "bar"), "foo")


def test_standalone_default():
    @func
    def f():
        pass

    assert f._standalone is False
    assert f().props.standalone is False


def test_standalone():
    @func(standalone=True)
    def f():
        pass

    assert f._standalone is True
    assert f().props.standalone is True


def test_resource_requirements():
    resource_requirements = ResourceRequirements(
        kubernetes=KubernetesResourceRequirements(node_selector={"a": "b"}, requests={})
    )

    @func(resource_requirements=resource_requirements, standalone=True)
    def f():
        pass

    assert f._resource_requirements == resource_requirements
    assert f().props.resource_requirements == resource_requirements


def test_resolve_error():
    @func()
    def f():
        raise ValueError("Intentional error")

    with pytest.raises(PipelineRunError) as exc_info:
        # resolving should surface the PipelineRunError,
        # with root cause as __context__
        # see https://peps.python.org/pep-0409/#language-details
        SilentRunner().run(f())

    assert isinstance(exc_info.value.__context__, FunctionError)
    assert isinstance(exc_info.value.__context__.__context__, ValueError)
    assert "Intentional error" in str(exc_info.value.__context__.__context__)


def test_calculate_error():
    @func()
    def f():
        raise ValueError("Intentional error")

    with pytest.raises(FunctionError) as exc_info:
        # calling calculate should surface the FunctionError,
        # with root cause as __context__
        # see https://peps.python.org/pep-0409/#language-details
        f.execute()

    assert isinstance(exc_info.value.__context__, ValueError)
    assert "Intentional error" in str(exc_info.value.__context__)


@func
def pass_through(x: int) -> int:
    return x


@func
def unused_results_pipeline() -> int:
    x = pass_through(42)
    y = pass_through(x)
    pass_through(y)
    return y


@func
def unused_results_list_pipeline(create_unused: bool) -> List[int]:
    x = pass_through(42)
    y = pass_through(43)
    z = pass_through(44)
    if create_unused:
        return [x, y]
    else:
        return [x, y, z]


def test_unused_future():
    with pytest.raises(PipelineRunError, match=r".*output.*does not depend on.*"):
        SilentRunner().run(unused_results_pipeline())
    with pytest.raises(PipelineRunError, match=r".*output.*does not depend on.*"):
        SilentRunner().run(unused_results_list_pipeline(True))
    SilentRunner().run(unused_results_list_pipeline(False))
