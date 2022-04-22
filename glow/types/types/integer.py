# Standard library
import typing

# Glow
from glow.types.type import Type, is_type, NotAGlowTypeError


class Integer(Type, int):
    """
    Glow type representing a Python `int`.
    """

    # Required to override Type.__init__
    def __init__(self, value):
        super().__init__()

    @classmethod
    def safe_cast(
        cls, value: typing.Any
    ) -> typing.Tuple[typing.Optional["Integer"], typing.Optional[str]]:
        try:
            return cls(value), None
        except ValueError as exception:
            return None, str(exception)

    @classmethod
    def can_cast_type(
        cls, type_: typing.Type[Type]
    ) -> typing.Tuple[bool, typing.Optional[str]]:
        if not is_type(type_):
            raise NotAGlowTypeError(type_)

        # Using `float` to avoid circular dependency with `Float`
        if issubclass(type_, float):
            return True, None

        if issubclass(type_, Integer):
            return True, None

        return False, "{} cannot cast to Integer".format(type_)

    # This is necessary to satisy mypy when using +
    # and the calculator output type is Integer

    def __add__(self, x: int) -> "Integer":
        if isinstance(x, int):
            return Integer(super().__add__(x))

        return NotImplemented

    def __sub__(self, x: int) -> "Integer":
        if isinstance(x, int):
            return Integer(super().__sub__(x))

        return NotImplemented

    def __mul__(self, x) -> "Integer":
        if isinstance(x, int):
            return Integer(super().__mul__(x))

        return NotImplemented

    def __truediv__(self, x) -> "Integer":
        if isinstance(x, int):
            return Integer(super().__truediv__(x))

        return NotImplemented
