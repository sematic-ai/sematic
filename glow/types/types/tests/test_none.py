# Glow
from glow.types.casting import safe_cast, can_cast_type


def test_safe_cast():
    assert safe_cast(None, type(None)) == (None, None)
    assert safe_cast(42, type(None)) == (None, "42 is not None")


def test_can_cast_type():
    assert can_cast_type(type(None), type(None)) == (True, None)
    assert can_cast_type(int, type(None)) == (
        False,
        "Cannot cast <class 'int'> to NoneType",
    )
