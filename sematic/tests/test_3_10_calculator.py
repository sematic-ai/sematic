# Third-party
import pytest

# Sematic
from sematic.calculator import Calculator, func


def test_decorator_3_10_style_hints():
    @func
    def f(a: list[int], b: dict[str, str]) -> int | float:
        return 42

    assert isinstance(f, Calculator)
    result = f([1, 2, 3], {"hi": "there"}).resolve(tracking=False)
    assert result == 42


def test_decorator_unparameterized_generic():
    expected_exception = (
        r"Invalid type annotation for argument 'a' of "
        r"sematic.tests.test_3_10_calculator.f: "
        r"list must be parametrized \(list\[...\] instead of list\)."
    )
    with pytest.raises(TypeError, match=expected_exception):

        @func
        def f(a: list) -> int:
            return 42
