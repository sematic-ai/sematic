# Standard Library
import re
import typing

# Third-party
import pytest

# Sematic
from sematic.types.casting import can_cast_type, cast, safe_cast
from sematic.types.registry import (
    is_parameterized_generic,
    register_can_cast,
    register_safe_cast,
)


def test_safe_cast_different_classes():
    class A:
        pass

    class B:
        pass

    cast_value, error = safe_cast(B(), A)

    assert cast_value is None
    assert re.match("Cannot cast .*B object.* to .*A", error)


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


def test_is_parameterized_generic():
    assert is_parameterized_generic(int) is False
    assert is_parameterized_generic(typing.List[int]) is True
    assert is_parameterized_generic(typing.Set[int]) is True
    assert is_parameterized_generic(typing.Optional[int]) is True

    with pytest.raises(TypeError, match="must be parametrized"):
        is_parameterized_generic(typing.List, raise_for_unparameterized=True)

    with pytest.raises(TypeError, match="must be parametrized"):
        is_parameterized_generic(typing.Set, raise_for_unparameterized=True)

    with pytest.raises(TypeError, match="must be parametrized"):
        is_parameterized_generic(typing.Optional, raise_for_unparameterized=True)
