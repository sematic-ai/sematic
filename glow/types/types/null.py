import typing
from glow.types.type import Type


class Null(Type):
    """
    glow type representing null values (`None` in Python).

    This type cannot be instantiated.
    """

    @classmethod
    def has_instances(cls) -> bool:
        return False

    @classmethod
    def safe_cast(
        cls, value: typing.Any
    ) -> typing.Tuple[typing.Optional[typing.Any], typing.Optional[str]]:
        if value is None:
            return None, None

        return None, "{} is not of type {}".format(repr(value), cls.__name__)

    @classmethod
    def can_cast_type(
        cls, type_: typing.Type[Type]
    ) -> typing.Tuple[bool, typing.Optional[str]]:
        pass
