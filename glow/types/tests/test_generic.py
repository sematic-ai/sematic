# Standard library
import collections

# Third-party
import pytest

# Glow
from glow.types.generic_type import GenericType
from glow.types.casting import can_cast_type, safe_cast


class SomeGenericType(GenericType):
    @classmethod
    def parametrize(cls, args):
        return collections.OrderedDict(
            (
                ("foo", args[0]),
                ("bar", args[1]),
            )
        )

    @classmethod
    def safe_cast(cls, value):  # noqa: F811
        values = cls.get_parameters().values()
        if value in cls.get_parameters().values():
            return value, None

        return None, "value not in {}".format(tuple(values))

    @classmethod
    def can_cast_type(cls, type_):  # noqa: F811
        if issubclass(type_, SomeGenericType):
            values = type_.get_parameters().values()
            allowed_values = cls.get_parameters().values()
            if set(values) == set(allowed_values):
                return True, None

        return False, "Incompatible values"


def test_parameters():
    type_ = SomeGenericType[12, 34]

    parameters = type_.get_parameters()
    assert isinstance(parameters, collections.OrderedDict)

    assert parameters == dict(foo=12, bar=34)


@pytest.mark.parametrize(
    "value, expected_value, error, expected_value2, error2",
    (
        (12, 12, None, None, "value not in (34, 56)"),
        (34, 34, None, 34, None),
        (56, None, "value not in (12, 34)", 56, None),
    ),
)
def test_safe_cast(value, expected_value, error, expected_value2, error2):
    type_ = SomeGenericType[12, 34]
    # Testing that a different parametrization does not override casting
    # functions in the registry
    type2 = SomeGenericType[34, 56]

    assert safe_cast(value, type_) == (expected_value, error)
    assert safe_cast(value, type2) == (expected_value2, error2)


def test_can_cast_type():
    assert can_cast_type(SomeGenericType[34, 56], SomeGenericType[34, 56]) == (
        True,
        None,
    )

    assert can_cast_type(SomeGenericType[34, 56], SomeGenericType[32, 57]) == (
        False,
        "Incompatible values",
    )
