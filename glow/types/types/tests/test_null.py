# Third party
import pytest

# Glow
from glow.types.type import NotAGlowTypeError
from glow.types.types.null import Null
from glow.types.types.float import Float


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


class SubNull(Null):
    pass


@pytest.mark.parametrize(
    "type_, expected_can_cast, expected_err",
    (
        (Null, True, None),
        (SubNull, True, None),
        (Float, False, "Float cannot cast to Null"),
    ),
)
def test_can_cast_type(type_, expected_can_cast, expected_err):
    can_cast, err = Null.can_cast_type(type_)
    assert can_cast is expected_can_cast
    assert err == expected_err


def test_can_cast_type_non_type():
    with pytest.raises(NotAGlowTypeError, match="<class 'int'> is not a Glow type"):
        Null.can_cast_type(int)
