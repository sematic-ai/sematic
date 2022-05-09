import abc
import typing


class TypeMeta(abc.ABCMeta):

    # Defined here to satisfy mypy
    # Although it is not incorrect
    def safe_cast(
        cls, value: typing.Any
    ) -> typing.Tuple[typing.Any, typing.Optional[str]]:
        raise NotImplementedError()

    def can_cast_type(cls, type_: type) -> typing.Tuple[bool, typing.Optional[str]]:
        raise NotImplementedError


class Type(abc.ABC, metaclass=TypeMeta):
    """
    Abstract base class to represent a Type.
    """

    def __init__(self):
        if self.__class__.has_instances() is False:
            raise RuntimeError(
                "Type {} cannot be instantiated".format(self.__class__.__name__)
            )

    @classmethod
    def has_instances(cls) -> bool:
        return True

    @classmethod
    @abc.abstractmethod
    def safe_cast(
        cls, value: typing.Any
    ) -> typing.Tuple[typing.Optional[typing.Any], typing.Optional[str]]:
        pass

    @classmethod
    @abc.abstractmethod
    def can_cast_type(cls, type_: type) -> typing.Tuple[bool, typing.Optional[str]]:
        pass


def is_type(type_: type) -> bool:
    if not isinstance(type_, type):
        raise ValueError("{} is not a Python type".format(type_))

    return issubclass(type_, Type)


class NotAGlowTypeError(TypeError):

    _NOT_A_GLOW_TYPE_ERROR = "{} is not a Glow type. See https://docs."

    def __init__(self, type_: typing.Any):
        super().__init__(self._NOT_A_GLOW_TYPE_ERROR.format(type_))
