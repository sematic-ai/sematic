# Standard library
import json
import typing

# Third-party
import cloudpickle  # type: ignore

# Glow
from glow.types.registry import (
    get_to_binary_func,
    get_from_binary_func,
    register_to_binary,
    register_from_binary,
)


# type_ must be `typing.Any` because `typing` aliases are not type
def to_binary(value: typing.Any, type_: typing.Any) -> bytes:
    """
    Converts a value into a binary serialization.
    """
    to_binary_func = get_to_binary_func(type_)

    if to_binary_func is not None:
        return to_binary_func(value, type_)

    return cloudpickle.dumps(value)


def from_binary(binary: bytes, type_: typing.Any) -> typing.Any:
    from_binary_func = get_from_binary_func(type_)

    if from_binary_func is not None:
        return from_binary_func(binary, type)

    return cloudpickle.loads(binary)


def to_binary_json(value: typing.Any) -> bytes:
    return json.dumps(value, sort_keys=True).encode("utf-8")


def from_binary_json(binary: bytes) -> typing.Any:
    return json.loads(binary.decode("utf-8"))


RegisteredType = typing.TypeVar("RegisteredType", bound=type)


def serializes_to_json(type_: RegisteredType) -> None:
    """
    registers a type to serialize to JSON
    """

    @register_to_binary(type_)
    def _to_binary(value: RegisteredType, _) -> bytes:
        return to_binary_json(value)

    @register_from_binary(type_)
    def _from_binary(binary: bytes, _) -> RegisteredType:
        value = from_binary_json(binary)
        value = typing.cast(RegisteredType, value)
        return value
