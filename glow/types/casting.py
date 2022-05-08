# Standard Library
import typing

# Glow
from glow.types.registry import CAN_CAST_REGISTRY, SAFE_CAST_REGISTRY


def can_cast_type(
    from_type: type, to_type: type
) -> typing.Tuple[bool, typing.Optional[str]]:
    # Should this be `if issubclass(from_type, to_type)`
    # Can instances of subclasses always cast to their parents?
    if from_type is to_type:
        return True, None

    if to_type in CAN_CAST_REGISTRY:
        _can_cast_func = CAN_CAST_REGISTRY[to_type]
        return _can_cast_func(from_type)

    return False, "{} cannot cast to {}".format(from_type, to_type)


def safe_cast(
    value: typing.Any, type_: type
) -> typing.Tuple[typing.Any, typing.Optional[str]]:
    if isinstance(value, type_):
        return value, None

    if type_ in SAFE_CAST_REGISTRY:
        _safe_cast_func = SAFE_CAST_REGISTRY[type_]
        return _safe_cast_func(value)

    return None, "Can't cast {} to {}".format(value, type_)


def cast(value: typing.Any, type_: type) -> typing.Any:
    cast_value, error = safe_cast(value, type_)

    if error is not None:
        raise TypeError("Cannot cast {} to {}: {}".format(value, type_.__name__, error))

    return cast_value
