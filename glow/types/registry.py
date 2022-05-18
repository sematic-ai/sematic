# Standard library
import typing

# Glow
from glow.types.generic_type import GenericType


# TYPE CASTING


# Input type has to be `typing.Any` because `typing.List` is not a `type`
CanCastTypeCallable = typing.Callable[
    [typing.Any, typing.Any], typing.Tuple[bool, typing.Optional[str]]
]


_CAN_CAST_REGISTRY: typing.Dict[type, CanCastTypeCallable] = {}


def register_can_cast(
    *types: type,
) -> typing.Callable[[CanCastTypeCallable], CanCastTypeCallable]:
    """
    Register a `can_cast_type` function for type `type_`.
    """

    def _register_can_cast(func: CanCastTypeCallable) -> CanCastTypeCallable:
        # ToDo(@neutralino1): validate func signature
        for type_ in types:
            _CAN_CAST_REGISTRY[type_] = func

        return func

    return _register_can_cast


# Input type has to be `typing.Any` because `typing.List` is not a `type`
def get_can_cast_func(type_: typing.Any) -> typing.Optional[CanCastTypeCallable]:
    """
    Obtain the registered `can_cast_type` logic for `type_`.
    """
    return _get_registered_func(_CAN_CAST_REGISTRY, type_)


# VALUE CASTING


SafeCastCallable = typing.Callable[
    [typing.Any, typing.Any], typing.Tuple[typing.Any, typing.Optional[str]]
]


_SAFE_CAST_REGISTRY: typing.Dict[type, SafeCastCallable] = {}


def register_safe_cast(
    *types: type,
) -> typing.Callable[[SafeCastCallable], SafeCastCallable]:
    """
    Register a `safe_cast` function for type `type_`.
    """

    def _register_can_cast(func: SafeCastCallable) -> SafeCastCallable:
        # Todo(@neutralino1): validate func signature
        for type_ in types:
            _SAFE_CAST_REGISTRY[type_] = func

        return func

    return _register_can_cast


def get_safe_cast_func(type_: typing.Any) -> typing.Optional[SafeCastCallable]:
    """
    Obtain a `safe_cast` function for type `type_`.
    """
    return _get_registered_func(_SAFE_CAST_REGISTRY, type_)


# BINARY SERIALIZATION

ToBinaryCallable = typing.Callable[[typing.Any, typing.Any], bytes]


_TO_BINARY_REGISTRY: typing.Dict[type, ToBinaryCallable] = {}


def register_to_binary(
    type_: type,
) -> typing.Callable[[ToBinaryCallable], ToBinaryCallable]:
    """
    Decorator to register a function to convert `type_` to a binary payload for
    serialization.
    """

    def _register_to_binary(func: ToBinaryCallable) -> ToBinaryCallable:
        # ToDo(@neutralino1): validate func signature
        _TO_BINARY_REGISTRY[type_] = func

        return func

    return _register_to_binary


def get_to_binary_func(type_: typing.Any) -> typing.Optional[ToBinaryCallable]:
    """
    Obtain the serialization functionf or `type_`.
    """
    return _get_registered_func(_TO_BINARY_REGISTRY, type_)


FromBinaryCallable = typing.Callable[[bytes, typing.Any], typing.Any]


_FROM_BINARY_REGISTRY: typing.Dict[type, FromBinaryCallable] = {}


def register_from_binary(
    type_: type,
) -> typing.Callable[[FromBinaryCallable], FromBinaryCallable]:
    """
    Decorator to register a deserilization function for `type_`.
    """

    def _register_from_binary(func: FromBinaryCallable) -> FromBinaryCallable:
        # ToDo(@neutralino1): validate func signature
        _FROM_BINARY_REGISTRY[type_] = func

        return func

    return _register_from_binary


def get_from_binary_func(type_: typing.Any) -> typing.Optional[FromBinaryCallable]:
    """
    Obtain the deserialization function for `type_`.
    """
    return _get_registered_func(_FROM_BINARY_REGISTRY, type_)


# TOOLS


RegisteredFunc = typing.TypeVar("RegisteredFunc")


def _get_registered_func(
    registry: typing.Dict[type, RegisteredFunc], type_: typing.Any
) -> typing.Optional[RegisteredFunc]:
    """
    Obtain a registered function (casting, serialization) from a registry.
    """
    registry_type = get_origin_type(type_)

    return registry.get(registry_type)


def get_origin_type(type_: typing.Any) -> typing.Any:
    """
    Extract the type by which the casting and serialization logic
    is indexed.

    Typically that is the type, except for type aliases (e.g. `List[int]`)
    where we extract the origin type (e.g. `list`).
    """
    registry_type = type_
    if is_valid_typing_alias(registry_type) or is_glow_parametrized_generic_type(
        registry_type
    ):
        registry_type = registry_type.__origin__
    return registry_type


def is_valid_typing_alias(type_: typing.Any) -> bool:
    """
    Is this a `typing` type, and if so, is it correctly subscribed?
    """
    if isinstance(
        type_,
        (
            typing._GenericAlias,  # type: ignore
            typing._UnionGenericAlias,  # type: ignore
            typing._CallableGenericAlias,  # type: ignore
        ),
    ):
        return True

    if isinstance(type_, (typing._SpecialForm, typing._BaseGenericAlias)):  # type: ignore
        raise ValueError("{} must be parametrized")

    return False


def is_glow_parametrized_generic_type(type_: typing.Any) -> bool:
    return (
        isinstance(type_, type)
        and issubclass(type_, GenericType)
        and GenericType.PARAMETERS_KEY in type_.__dict__
    )
