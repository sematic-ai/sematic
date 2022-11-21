# Third-party
import pytest

# Sematic
from sematic.types.type import Type, is_type


def test_is_type_true():
    class SomeType(Type):
        pass

    assert is_type(SomeType) is True


def test_is_type_false():
    class SomeType:
        pass

    assert is_type(SomeType) is False


def test_is_type_non_type():
    with pytest.raises(ValueError, match="is not a Python type"):
        is_type("abc")


def test_has_instances_false():
    class NoInstancesType(Type):
        @classmethod
        def has_instances(cls):
            return False

        @classmethod
        def safe_cast(cls, _):
            pass

        @classmethod
        def can_cast_type(cls, _):
            pass

    with pytest.raises(
        RuntimeError, match="Type NoInstancesType cannot be instantiated"
    ):
        NoInstancesType()


def test_has_instances_true():
    class YesInstancesType(Type):
        @classmethod
        def safe_cast(cls, _):
            pass

        @classmethod
        def can_cast_type(cls, _):
            pass

    assert isinstance(YesInstancesType(), YesInstancesType)
