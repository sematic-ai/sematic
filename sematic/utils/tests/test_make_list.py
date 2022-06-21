# Standard Library
from typing import List, Union

# Sematic
from sematic.future import Future
from sematic.utils.make_list import make_list, convert_lists
from sematic.calculator import calculator
from sematic.db.tests.fixtures import test_db  # noqa: F401
from sematic.api.tests.fixtures import test_client, mock_requests  # noqa: F401


@calculator
def foo() -> str:
    return "foo"


@calculator
def bar() -> str:
    return "bar"


def test_make_list():
    future = make_list(List[str], [foo(), bar()])

    assert isinstance(future, Future)
    assert future.calculator.output_type is List[str]
    assert len(future.calculator.input_types) == 2


@calculator
def pipeline() -> List[str]:
    return make_list(List[str], [foo(), bar(), "baz"])


def test_pipeline(test_db, mock_requests):  # noqa: F811
    output = pipeline().resolve()
    assert output == ["foo", "bar", "baz"]


def test_convert_lists(test_db, mock_requests):  # noqa: F811
    result = convert_lists([1, foo(), [2, bar()], 3, [4, [5, foo()]]])

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
