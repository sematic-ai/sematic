# Standard library
import typing

# Input type has to be `typing.Any` because `typing.List` is not a `type`
CanCastTypeCallable = typing.Callable[
    [typing.Any, typing.Any], typing.Tuple[bool, typing.Optional[str]]
]


CAN_CAST_REGISTRY: typing.Dict[type, CanCastTypeCallable] = {}


def register_can_cast(
    type_: type,
) -> typing.Callable[[CanCastTypeCallable], CanCastTypeCallable]:
    def _register_can_cast(func: CanCastTypeCallable) -> CanCastTypeCallable:
        # ToDo(@neutralino1): validate func signature
        CAN_CAST_REGISTRY[type_] = func

        return func

    return _register_can_cast


SafeCastCallable = typing.Callable[
    [typing.Any, typing.Any], typing.Tuple[typing.Any, typing.Optional[str]]
]


SAFE_CAST_REGISTRY: typing.Dict[type, SafeCastCallable] = {}


def register_safe_cast(
    type_: type,
) -> typing.Callable[[SafeCastCallable], SafeCastCallable]:
    def _register_can_cast(func: SafeCastCallable) -> SafeCastCallable:
        # Todo(@neutralino1): validate func signature
        SAFE_CAST_REGISTRY[type_] = func

        return func

    return _register_can_cast
