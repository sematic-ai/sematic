# Standard library
import typing

# Glow
from glow.types.type import Type, is_type, NotAGlowTypeError


BOOL_TYPES = [bool]
try:
    # If numpy exists, we want to recognize numpy.bool_
    import numpy

    BOOL_TYPES.append(numpy.bool_)
except ImportError:
    pass

BOOL_TYPES = tuple(BOOL_TYPES)


class Boolean(Type):
    @classmethod
    def has_instances(cls) -> bool:
        return False

    @classmethod
    def safe_cast(
        cls, value: typing.Any
    ) -> typing.Tuple[typing.Optional[bool], typing.Optional[str]]:
        if isinstance(value, BOOL_TYPES):
            return value, None

        return None, "Only instances of bool can cast to Boolean. Got {}.".format(
            repr(value)
        )

    @classmethod
    def can_cast_type(
        cls, type_: typing.Type[Type]
    ) -> typing.Tuple[bool, typing.Optional[str]]:
        if not is_type(type_):
            raise NotAGlowTypeError(type_)

        if issubclass(type_, Boolean):
            return True, None

        return False, "{} cannot cast to Boolean".format(type_)
