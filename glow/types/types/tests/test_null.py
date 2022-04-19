import pytest

from glow.types.types.null import Null


def test_instanciation():
    with pytest.raises(RuntimeError, match="Type Null cannot be instantiated"):
        Null()


def test_safe_cast_pass():
    cast_value, error = Null.safe_cast(None)
    assert cast_value is None
    assert error is None


def test_safe_cast_fail():
    cast_value, error = Null.safe_cast("abc")
    assert cast_value is None
    assert error == "'abc' is not of type Null"
