# Standard library
import abc
import typing
import collections
import copy

# Sematic
from sematic.types.type import Type, TypeMeta


class GenericMeta(TypeMeta):
    """
    Meta-class for GenericType. A meta-class is required to enable the `getitem`
    API on generic types (square bracket notation to parametrize generics).
    """

    PARAMETERS_KEY = "_parameters"

    def __getitem__(cls, args) -> "GenericMeta":
        parameters = cls.parametrize(args)
        return cls.make_type(parameters)

    # Defined here for consistency, since used in __getitem__
    # See GenericType for documentation.
    def parametrize(cls, args) -> typing.OrderedDict[str, typing.Any]:
        raise NotImplementedError()

    # To satisfy mypy
    def get_parameters(cls) -> typing.OrderedDict[str, typing.Any]:
        raise NotImplementedError()

    def make_type(
        cls, parameters: typing.OrderedDict[str, typing.Any]
    ) -> "GenericMeta":
        if not isinstance(parameters, collections.OrderedDict):
            raise TypeError(
                (
                    "Incorrect generic type implementation for {}."
                    " parameters should be a collections.OrderedDict."
                    " See https://docs"
                )
            )

        type_ = GenericMeta(
            str(
                "{name}[{parameters}]".format(
                    name=cls.__name__,
                    parameters=", ".join(map(repr, parameters.values())),
                )
            ),
            (cls,),
            {
                "__module": cls.__module__,
                cls.PARAMETERS_KEY: parameters,
                # this mirrors the behavior of `typing` generics
                "__origin__": cls,
            },
        )

        return type_


class GenericType(Type, metaclass=GenericMeta):
    """
    Abstract base class for Sematic generic types.

    Generic types are types that can be parametrized to create a specific type.

    For an example, see `FloatInRange`.

    To create a generic type, simply inherit from `GenericType` and implement
    the `parametrize` API.
    """

    # Parametrization of the generic type
    # Private, use get_parameters API to access parameters.
    _parameters: typing.Optional[typing.OrderedDict[str, typing.Any]] = None

    @classmethod
    @abc.abstractmethod
    def parametrize(cls, args: typing.Tuple) -> typing.OrderedDict[str, typing.Any]:
        """
        This is the method that defines the parameter dictionary for generic
        types.

        The method must return a `collections.OrderedDict` so that type
        serialization is deterministic.

        This method should contain all the validation logic for input
        parameters, as well as setting defaults for optional parameters.

        The returned dictionary should be JSON-encodable.

        Parameters
        ----------
        args: typing.Tuple
            A tuple of arguments as they were passed by the user to the []
            operator.
        """
        pass

    @classmethod
    def get_parameters(cls) -> typing.OrderedDict[str, typing.Any]:
        """
        Get this type's parameters.

        Raises
        ------
        TypeError: if the type is not yet parametrized.
        """
        if cls._parameters is None:
            raise TypeError("{} was not parametrized.".format(cls.__name__))

        return copy.deepcopy(cls._parameters)
