# Standard library
import re
import typing

# Third-party
import pytest

# Glow
from glow.types.casting import can_cast_type, safe_cast, cast, _is_valid_typing
from glow.types.registry import register_can_cast, register_safe_cast


def test_safe_cast_different_classes():
    class A:
        pass

    class B:
        pass

    cast_value, error = safe_cast(B(), A)

    assert cast_value is None
    assert re.match("Can't cast .*B object.* to .*A", error)


def test_safe_cast_same_class():
    class A:
        pass

    value = A()

    cast_value, error = safe_cast(value, A)

    assert cast_value is value
    assert error is None


def test_safe_cast_subclass():
    class Parent:
        pass

    class Child(Parent):
        pass

    value = Child()

    cast_value, error = safe_cast(value, Parent)

    assert cast_value is value
    assert error is None


def test_safe_cast_registered():
    class A:
        def __init__(self, value):
            self.value = value

    @register_safe_cast(A)
    def _safe_cast_to_A(value, _):
        return A(value), None

    cast_value, error = safe_cast(42, A)

    assert isinstance(cast_value, A)
    assert cast_value.value == 42
    assert error is None


def test_cast():
    class A:
        pass

    with pytest.raises(TypeError, match="Cannot cast"):
        cast(42, A)

    cast_value = cast(42, int)

    assert isinstance(cast_value, int)
    assert cast_value == 42


def test_can_cast_type_same_type():
    class A:
        pass

    assert can_cast_type(A, A) == (True, None)


def test_can_cast_type_different_types():
    class A:
        pass

    class B:
        pass

    can_cast, error = can_cast_type(A, B)

    assert can_cast is False
    assert re.match(".*A'> cannot cast to .*B'>", error)


def test_can_cast_type_registered():
    class A:
        pass

    class B:
        pass

    @register_can_cast(B)
    def _can_cast_type_to_b(type_, _):
        return True, None

    assert can_cast_type(A, B) == (True, None)


def test_is_valid_typing():
    assert _is_valid_typing(int) is False
    assert _is_valid_typing(typing.List[int]) is True
    assert _is_valid_typing(typing.Optional[int]) is True

    with pytest.raises(ValueError, match="must be parametrized"):
        _is_valid_typing(typing.List)

    with pytest.raises(ValueError, match="must be parametrized"):
        _is_valid_typing(typing.Optional)
