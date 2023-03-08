# Standard Library
import abc
import sys
import typing

if (sys.version_info.major, sys.version_info.minor) >= (3, 10):
    # Standard Library
    from types import UnionType  # type: ignore
else:
    # Different types from the typing module have different behaviors
    # when getting origin--behaviors which differ with python version.
    # Rather than hard-coding what the origin type is when you have
    # parameterized a Union, we just use an example. Why use two types
    # instead of just Union[int]? Because that is disallowed--all Union
    # parameterizations must have at least two types.
    UnionType = typing.get_origin(typing.Union[int, float])  # type: ignore


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


def get_origin(type_: typing.Any) -> typing.Optional[typing.Type[typing.Any]]:
    """Replacement for typing.get_origin that treats union expressions like typing.Union.

    Union expressions are supported only in python 3.10 and greater.
    Using this function, get_origin(int | float) will give the same
    result as get_origin(Union[int, float]).

    Parameters
    ----------
    type_:
        An object which may be a type

    Returns
    -------
    If the object is a type that is parameterized, returns the origin type.
    Otherwise returns None.
    """
    builtin_origin = typing.get_origin(type_)
    if builtin_origin == UnionType:
        return typing.get_origin(typing.Union[int, float])
    return builtin_origin
