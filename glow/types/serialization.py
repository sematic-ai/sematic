"""
This module contains the public API for artifact serialization.
"""
# Standard library
import abc
import base64
import collections
import importlib
import inspect
import json
import typing


# Third-party
import cloudpickle  # type: ignore

# Glow
from glow.types.registry import (
    get_to_binary_func,
    get_from_binary_func,
    is_glow_parametrized_generic_type,
    is_valid_typing_alias,
    register_to_binary,
    register_from_binary,
    get_origin_type,
)
from glow.types.generic_type import GenericType


# VALUE SERIALIZATION


# type_ must be `typing.Any` because `typing` aliases are not type
def to_binary(value: typing.Any, type_: typing.Any) -> bytes:
    """
    Public API to serialize `value` to binary using the
    serialization logic of `type_`.
    """
    # First we check if there is a registered serialization
    # function for type_.
    to_binary_func = get_to_binary_func(type_)

    if to_binary_func is not None:
        return to_binary_func(value, type_)

    # If not, we use cloudpickle.
    return cloudpickle.dumps(value)


def from_binary(binary: bytes, type_: typing.Any) -> typing.Any:
    """
    Public API to deserialize a binary blob into its
    corresponding value using the deserialization of `type_`.
    """
    # First we check whether this is a registered serialization
    # function for type_.
    from_binary_func = get_from_binary_func(type_)

    if from_binary_func is not None:
        return from_binary_func(binary, type)

    # Otherwise we try pickle.
    return cloudpickle.loads(binary)


RegisteredType = typing.TypeVar("RegisteredType", bound=type)


SERIALIZES_TO_JSON: typing.Set[type] = set()


def serializes_to_json(type_: RegisteredType) -> None:
    """
    registers a type to serialize to JSON.

    This is a shortcut for all types that can natively
    serialization to JSON (e.g. `int`, `float`, `str`, etc.)
    """

    @register_to_binary(type_)
    def _to_binary(value: RegisteredType, _) -> bytes:
        return to_binary_json(value)

    @register_from_binary(type_)
    def _from_binary(binary: bytes, _) -> RegisteredType:
        value = from_binary_json(binary)
        value = typing.cast(RegisteredType, value)
        return value

    SERIALIZES_TO_JSON.add(type_)


def does_serialize_to_json(type_: type) -> bool:
    return type_ in SERIALIZES_TO_JSON


def to_binary_json(value: typing.Any) -> bytes:
    return json.dumps(value, sort_keys=True).encode("utf-8")


def from_binary_json(binary: bytes) -> typing.Any:
    return json.loads(binary.decode("utf-8"))


def binary_to_string(binary: bytes) -> str:
    return base64.b64encode(binary).decode("ascii")


# TYPE SERIALIZATION


def type_to_json_encodable(type_: typing.Any) -> typing.Dict[str, typing.Any]:

    registry: collections.OrderedDict[str, typing.Any] = collections.OrderedDict()

    _populate_registry(type_, registry)

    return collections.OrderedDict(
        (
            ("type", _type_repr(type_)),
            ("registry", registry),
        )
    )


def _populate_registry(
    type_: typing.Any, registry: collections.OrderedDict[str, typing.Any]
) -> None:
    def _include_in_registry(t) -> bool:
        if t in (object, abc.ABC, GenericType):
            return False

        return True

    if not _include_in_registry(type_):
        return

    type_key = _get_key(type_)

    if is_glow_parametrized_generic_type(type_):
        _populate_registry_from_parameters(type_.get_parameters(), registry)

    if is_valid_typing_alias(type_):
        _populate_registry_from_parameters(type_.__args__, registry)

    registry[type_key] = []

    bases: typing.Tuple[type, ...] = tuple()
    try:
        bases = type_.__bases__
    except AttributeError:
        pass

    for parent_type in bases:
        if not _include_in_registry(parent_type):
            continue

        _populate_registry(parent_type, registry)

        if issubclass(
            parent_type, GenericType
        ) and not is_glow_parametrized_generic_type(parent_type):
            continue

        registry[type_key].append(_type_repr(parent_type))


def _populate_registry_from_parameters(parameters, registry):
    if isinstance(parameters, type) or is_valid_typing_alias(parameters):
        _populate_registry(parameters, registry)

    if isinstance(parameters, _BUILTINS):
        return

    if isinstance(parameters, typing.Sequence):
        for parameter in parameters:
            _populate_registry_from_parameters(parameter, registry)

    if isinstance(parameters, typing.Mapping):
        for parameter in parameters.values():
            _populate_registry_from_parameters(parameter, registry)


def _type_repr(
    type_: typing.Any,
) -> typing.Tuple[typing.Optional[str], str, typing.Any]:
    return (_get_category(type_), _get_key(type_), _get_parameters(type_))


_BUILTINS = (float, int, str, bool, type(None), bytes)


def _is_builtin(type_: typing.Any):
    return type_ in _BUILTINS


def _get_category(type_: typing.Any) -> typing.Optional[str]:
    if _is_builtin(type_):
        return "builtins"

    if is_valid_typing_alias(type_):
        return "typing"

    return None


_SPECIAL_FORM_MAPPING = {
    typing.Union: "Union",
}


def _get_key(type_: typing.Any) -> str:
    """
    Get a unique str key for a given type.

    For most types (builtins, classes, etc) the key is simply
    the name of the type (`int`, `float`, `NoneType`, `str`, `bool`, etc.).

    For subscripted generics, it is the name of the __origin__ type. For example:
     `typing.List[int]` -> `list`, `Union[int, float]` -> `Union`, etc.
    """
    # We want the unsubscripted or parametrized generic
    origin_type = get_origin_type(type_)

    try:
        # Most have a __name__ attribute
        return origin_type.__name__
    except AttributeError:
        pass

    # instances of `typing._SpecialForm` don't have __name__
    if origin_type in _SPECIAL_FORM_MAPPING:
        return _SPECIAL_FORM_MAPPING[origin_type]

    raise Exception("Unable to get type key for: {}".format(type_))


def _get_parameters(type_: typing.Any) -> typing.Optional[typing.Dict[str, typing.Any]]:
    if is_valid_typing_alias(type_):
        return {"args": [_parameter_repr(arg) for arg in type_.__args__]}

    if is_glow_parametrized_generic_type(type_):
        return {
            "parameters": collections.OrderedDict(
                (
                    (key, _parameter_repr(param))
                    for key, param in type_.get_parameters().items()
                )
            )
        }

    return None


def _parameter_repr(value: typing.Any) -> typing.Any:
    def _is_type(type_) -> bool:
        return (
            _is_builtin(value)
            or is_valid_typing_alias(value)
            or is_glow_parametrized_generic_type(value)
        )

    if _is_type(value):
        return {"type": _type_repr(value)}

    def _is_scalar(v):
        # is not a type or a class or a function or a sequence or a mapping
        return (
            (isinstance(v, str) or not isinstance(v, (typing.Sequence, typing.Mapping)))
            and not _is_type(v)
            and not inspect.isclass(v)
            and not inspect.isfunction(v)
        )

    if isinstance(value, typing.Sequence):
        if any(not _is_scalar(item) for item in value):
            return list(map(_parameter_repr, value))

    if isinstance(value, typing.Mapping):
        if any(not _is_scalar(item) for item in value.values()):
            return collections.OrderedDict(
                ((k, _parameter_repr(v)) for k, v in value.items())
            )

    if inspect.isclass(value) or inspect.isfunction(value):
        name, module = value.__name__, value.__module__
        _assert_can_import(name, module)
        return {"import": (name, module)}

    return {"value": value}


def _assert_can_import(name, module_path):
    module = importlib.import_module(module_path)
    obj = getattr(module, name)
    return obj
