import abc
import typing


class TypeMeta(abc.ABCMeta):
    """
    Metaclass for Type. Needed as a base class of GenericMeta.
    """

    pass


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


def is_type(type_: type) -> bool:
    if not isinstance(type_, type):
        raise ValueError("{} is not a Python type".format(type_))

    return issubclass(type_, Type)


class NotASematicTypeError(TypeError):

    _NOT_A_SEMATIC_TYPE_ERROR = "{} is not a Sematic type. See https://docs."

    def __init__(self, type_: typing.Any):
        super().__init__(self._NOT_A_SEMATIC_TYPE_ERROR.format(type_))
