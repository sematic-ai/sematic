import pytest

from glow.types.type import Type, is_type


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


def test_cast():
    class SomeType(Type):
        @classmethod
        def safe_cast(cls, value):
            if value is True:
                return "cast_value", None
            return None, "some error message"

    assert SomeType.cast(True) == "cast_value"

    with pytest.raises(
        TypeError, match="Cannot cast False to SomeType: some error message"
    ):
        SomeType.cast(False)


def test_cast_subclass():
    class ParentType(Type):
        @classmethod
        def safe_cast(cls, _):
            pass

    class ChildClass(ParentType):
        @classmethod
        def safe_cast(cls, _):
            pass

    assert isinstance(ParentType.cast(ChildClass()), ChildClass)


def test_has_instances_false():
    class NoInstancesType(Type):
        @classmethod
        def has_instances(cls):
            return False

        @classmethod
        def safe_cast(cls, _):
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

    assert isinstance(YesInstancesType(), YesInstancesType)
