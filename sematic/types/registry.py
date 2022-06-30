# Standard library
from typing import (  # type: ignore
    Any,
    Callable,
    Tuple,
    Optional,
    Dict,
    GenericAlias,
    _GenericAlias,
    _UnionGenericAlias,
    _CallableGenericAlias,
    _SpecialForm,
    _BaseGenericAlias,
    TypeVar,
    Union,
)

# Sematic
from sematic.types.generic_type import GenericType


RegistryKey = Union[type, _SpecialForm]


# TYPE CASTING


# Input type has to be `Any` because `List` is not a `type`
CanCastTypeCallable = Callable[[Any, Any], Tuple[bool, Optional[str]]]


_CAN_CAST_REGISTRY: Dict[RegistryKey, CanCastTypeCallable] = {}


def register_can_cast(
    *types: RegistryKey,
) -> Callable[[CanCastTypeCallable], CanCastTypeCallable]:
    """
    Register a `can_cast_type` function for type `type_`.
    """

    def _register_can_cast(func: CanCastTypeCallable) -> CanCastTypeCallable:
        # TODO(@neutralino1): validate func signature
        for type_ in types:
            _CAN_CAST_REGISTRY[type_] = func

        return func

    return _register_can_cast


# Input type has to be `Any` because `List` is not a `type`
def get_can_cast_func(type_: Any) -> Optional[CanCastTypeCallable]:
    """
    Obtain the registered `can_cast_type` logic for `type_`.
    """
    return _get_registered_func(_CAN_CAST_REGISTRY, type_)


# VALUE CASTING


SafeCastCallable = Callable[[Any, Any], Tuple[Any, Optional[str]]]


_SAFE_CAST_REGISTRY: Dict[RegistryKey, SafeCastCallable] = {}


def register_safe_cast(
    *types: RegistryKey,
) -> Callable[[SafeCastCallable], SafeCastCallable]:
    """
    Register a `safe_cast` function for type `type_`.
    """

    def _register_can_cast(func: SafeCastCallable) -> SafeCastCallable:
        # TODO(@neutralino1): validate func signature
        for type_ in types:
            _SAFE_CAST_REGISTRY[type_] = func

        return func

    return _register_can_cast


def get_safe_cast_func(type_: Any) -> Optional[SafeCastCallable]:
    """
    Obtain a `safe_cast` function for type `type_`.
    """
    return _get_registered_func(_SAFE_CAST_REGISTRY, type_)


# VALUE SERIALIZATION

ToJSONEncodableCallable = Callable[[Any, Any], Any]


_TO_JSON_ENCODABLE_REGISTRY: Dict[RegistryKey, ToJSONEncodableCallable] = {}


def register_to_json_encodable(
    *types: RegistryKey,
) -> Callable[[ToJSONEncodableCallable], ToJSONEncodableCallable]:
    """
    Decorator to register a function to convert `type_` to a JSON-encodable payload for
    serialization.
    """

    def _register_to_json_encodable(
        func: ToJSONEncodableCallable,
    ) -> ToJSONEncodableCallable:
        # TODO(@neutralino1): validate func signature
        for type_ in types:
            _TO_JSON_ENCODABLE_REGISTRY[type_] = func

        return func

    return _register_to_json_encodable


def get_to_json_encodable_func(
    type_: Any,
) -> Optional[ToJSONEncodableCallable]:
    """
    Obtain the serialization function for `type_`.
    """
    return _get_registered_func(_TO_JSON_ENCODABLE_REGISTRY, type_)


FromJSONEncodableCallable = Callable[[Any, Any], Any]


_FROM_JSON_ENCODABLE_REGISTRY: Dict[RegistryKey, FromJSONEncodableCallable] = {}


def register_from_json_encodable(
    *types: RegistryKey,
) -> Callable[[FromJSONEncodableCallable], FromJSONEncodableCallable]:
    """
    Decorator to register a deserilization function for `type_`.
    """

    def _register_from_json_encodable(
        func: FromJSONEncodableCallable,
    ) -> FromJSONEncodableCallable:
        # TODO(@neutralino1): validate func signature
        for type_ in types:
            _FROM_JSON_ENCODABLE_REGISTRY[type_] = func

        return func

    return _register_from_json_encodable


def get_from_json_encodable_func(
    type_: Any,
) -> Optional[FromJSONEncodableCallable]:
    """
    Obtain the deserialization function for `type_`.
    """
    return _get_registered_func(_FROM_JSON_ENCODABLE_REGISTRY, type_)


_JSON_ENCODABLE_SUMMARY_REGISTRY: Dict[RegistryKey, ToJSONEncodableCallable] = {}


def register_to_json_encodable_summary(
    *types: RegistryKey,
) -> Callable[[ToJSONEncodableCallable], ToJSONEncodableCallable]:
    """
    Decorator to register a function to convert `type_` to a JSON-encodable summary for
    the UI.
    """

    def _register_to_json_encodable_summary(
        func: ToJSONEncodableCallable,
    ) -> ToJSONEncodableCallable:
        # TODO(@neutralino1): validate func signature
        for type_ in types:
            _JSON_ENCODABLE_SUMMARY_REGISTRY[type_] = func

        return func

    return _register_to_json_encodable_summary


def get_to_json_encodable_summary_func(
    type_: Any,
) -> Optional[ToJSONEncodableCallable]:
    """
    Obtain the serialization function for `type_`.
    """
    return _get_registered_func(_JSON_ENCODABLE_SUMMARY_REGISTRY, type_)


# TOOLS


RegisteredFunc = TypeVar("RegisteredFunc")


def _get_registered_func(
    registry: Dict[RegistryKey, RegisteredFunc], type_: Any
) -> Optional[RegisteredFunc]:
    """
    Obtain a registered function (casting, serialization) from a registry.
    """
    registry_type = get_origin_type(type_)

    return registry.get(registry_type)


def get_origin_type(type_: Any) -> Any:
    """
    Extract the type by which the casting and serialization logic
    is indexed.

    Typically that is the type, except for type aliases (e.g. `List[int]`)
    where we extract the origin type (e.g. `list`).
    """
    registry_type = type_
    if is_valid_typing_alias(registry_type) or is_sematic_parametrized_generic_type(
        registry_type
    ):
        registry_type = registry_type.__origin__
    return registry_type


def is_valid_typing_alias(type_: Any) -> bool:
    """
    Is this a `typing` type, and if so, is it correctly subscribed?
    """
    if isinstance(
        type_,
        (
            GenericAlias,  # type: ignore
            _GenericAlias,  # type: ignore
            _UnionGenericAlias,  # type: ignore
            _CallableGenericAlias,  # type: ignore
        ),
    ):
        return True

    if isinstance(type_, (_SpecialForm, _BaseGenericAlias)):  # type: ignore
        raise ValueError("{} must be parametrized".format(type_))

    return False


def is_sematic_parametrized_generic_type(type_: Any) -> bool:
    try:
        return (
            issubclass(type_, GenericType)
            and GenericType.PARAMETERS_KEY in type_.__dict__
        )
    except Exception:
        return False


class DataclassKey:
    """
    This is solely to be used as indexation key in the registry for
    the default dataclass casting and serialization logics.
    """

    pass
