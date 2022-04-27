# Standard library
import pytest

# Glow
from glow.types.types.boolean import Boolean


def test_instantiation():
    with pytest.raises(RuntimeError, match="cannot be instantiated"):
        Boolean()


@pytest.mark.parametrize(
    "value, expected_cast_value, expected_err",
    (
        (True, True, None),
        (False, False, None),
        ("abc", None, "Only instances of bool can cast to Boolean. Got 'abc'."),
    ),
)
def test_safe_cast(value, expected_cast_value, expected_err):
    assert Boolean.safe_cast(value) == (expected_cast_value, expected_err)
