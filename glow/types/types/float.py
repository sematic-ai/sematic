import typing
from glow.types.type import Type, is_type


class Float(Type, float):
    """
    Glow type representing a Python `float`.
    """

    # Required to override Type.__init__
    def __init__(self, value):
        super().__init__()

    @classmethod
    def safe_cast(
        cls, value: typing.Any
    ) -> typing.Tuple[typing.Optional["Float"], typing.Optional[str]]:
        try:
            return cls(value), None
        except ValueError as exception:
            return None, str(exception)

    @classmethod
    def can_cast_type(
        cls, type_: typing.Type[Type]
    ) -> typing.Tuple[bool, typing.Optional[str]]:
        if not is_type(type_):
            raise TypeError("{} is not a Glow type".format(type_))

        if issubclass(type_, Float):
            return True, None

        # if issubclass(type_, Integer):
        #    return True, None

        return False, "{} cannot cast to Float".format(type_)

    # This is necessary to satisy mypy when using +
    # and the calculator output type is Float
    def __add__(self, __x: float) -> "Float":
        return Float(super().__add__(__x))

    def __mul__(self, __x: float) -> "Float":
        return Float(super().__mul__(__x))
