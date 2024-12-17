import sys

# Third-party
import pytest

# Sematic
from sematic.function import Function, func
from sematic.runners.silent_runner import SilentRunner


@pytest.mark.skipif(sys.version_info < (3, 10), reason="Requires python >=3.10")
def test_decorator_3_10_style_hints():
    @func
    def f(a: list[int], b: dict[str, str]) -> int | float:
        return 42

    assert isinstance(f, Function)
    result = SilentRunner().run(f([1, 2, 3], {"hi": "there"}))
    assert result == 42


def test_decorator_unparameterized_generic():
    expected_exception = (
        r"Invalid type annotation for argument 'a' of "
        r"sematic.tests.test_3_10_function.f: "
        r"list must be parametrized \(list\[...\] instead of list\)."
    )
    with pytest.raises(TypeError, match=expected_exception):

        @func
        def f(a: list) -> int:
            return 42
