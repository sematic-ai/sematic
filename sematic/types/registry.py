# Standard Library
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    TypeVar,
    Union,
    get_origin,
)

# Sematic
from sematic.types.generic_type import GenericType

_SUPPORTED_TYPES_DOCS = (
    "https://docs.sematic.dev/" "diving-deeper/type-support#what-types-are-supported"
)

# We only support a certain subset of annotations in typing,
# this lists them. It also includes the "origin" types they
# map to (which is essentially the unparameterized version
# of them; see python typing docs). The origin types are
# what we ant in the registry.
SUPPORTED_GENERIC_TYPING_ANNOTATIONS = {
    Tuple: get_origin(Tuple[int, int]),
    List: get_origin(List[int]),
    Dict: get_origin(Dict[int, int]),
    Union: get_origin(Union[int, str]),
    Optional: get_origin(Optional[int]),
}

# This is aliased to "Any" just because it can include pseudo-types in the form
# of things from the typing module that look like types but which are actually
# only meant for type hinting. Throughout this module, TypeAnnotation will be
# used in places where a type/supported typing annotation are expected. This
# aliasing doesn't do anything for mypy (it will use TypeAnnotation like Any),
# but does help convey intent for readers of the code.
TypeAnnotation = Any


# This is aliased to "Any" just because it can include pseudo-types in the form
# of things from the typing module that look like types but which are actually
# only meant for type hinting. This is slightly different from TypeAnnotation:
# where the former is used, all generics are expected to be parameterized (
# Union[int, float] is accepted, Union is not). Where this is used generics
# are expected NOT to be parameterized (Union[int, float] is not accepted,
# Union is).
RegistryKey = Any

# TYPE CASTING

CanCastTypeCallable = Callable[
    [TypeAnnotation, TypeAnnotation], Tuple[bool, Optional[str]]
]


_CAN_CAST_REGISTRY: Dict[RegistryKey, CanCastTypeCallable] = {}


def register_can_cast(
    *types: RegistryKey,
) -> Callable[[CanCastTypeCallable], CanCastTypeCallable]:
    """
    Register a `can_cast_type` function for type `type_`.
    """
    _validate_registry_keys(*types)

    def _register_can_cast(func: CanCastTypeCallable) -> CanCastTypeCallable:
        # TODO(@neutralino1): validate func signature
        for type_ in types:
            _CAN_CAST_REGISTRY[type_] = func

        return func

    return _register_can_cast


def get_can_cast_func(type_: TypeAnnotation) -> Optional[CanCastTypeCallable]:
    """
    Obtain the registered `can_cast_type` logic for `type_`.
    """
    validate_type_annotation(type_)
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
    _validate_registry_keys(*types)

    def _register_can_cast(func: SafeCastCallable) -> SafeCastCallable:
        # TODO(@neutralino1): validate func signature
        for type_ in types:
            _SAFE_CAST_REGISTRY[type_] = func

        return func

    return _register_can_cast


def get_safe_cast_func(type_: TypeAnnotation) -> Optional[SafeCastCallable]:
    """
    Obtain a `safe_cast` function for type `type_`.
    """
    validate_type_annotation(type_)
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
    _validate_registry_keys(*types)

    def _register_to_json_encodable(
        func: ToJSONEncodableCallable,
    ) -> ToJSONEncodableCallable:
        # TODO(@neutralino1): validate func signature
        for type_ in types:
            _TO_JSON_ENCODABLE_REGISTRY[type_] = func

        return func

    return _register_to_json_encodable


def get_to_json_encodable_func(
    type_: TypeAnnotation,
) -> Optional[ToJSONEncodableCallable]:
    """
    Obtain the serialization function for `type_`.
    """
    validate_type_annotation(type_)
    return _get_registered_func(_TO_JSON_ENCODABLE_REGISTRY, type_)


FromJSONEncodableCallable = Callable[[Any, Any], Any]


_FROM_JSON_ENCODABLE_REGISTRY: Dict[RegistryKey, FromJSONEncodableCallable] = {}


def register_from_json_encodable(
    *types: RegistryKey,
) -> Callable[[FromJSONEncodableCallable], FromJSONEncodableCallable]:
    """
    Decorator to register a deserilization function for `type_`.
    """
    _validate_registry_keys(*types)

    def _register_from_json_encodable(
        func: FromJSONEncodableCallable,
    ) -> FromJSONEncodableCallable:
        # TODO(@neutralino1): validate func signature
        for type_ in types:
            _FROM_JSON_ENCODABLE_REGISTRY[type_] = func

        return func

    return _register_from_json_encodable


def get_from_json_encodable_func(
    type_: TypeAnnotation,
) -> Optional[FromJSONEncodableCallable]:
    """
    Obtain the deserialization function for `type_`.
    """
    validate_type_annotation(type_)
    return _get_registered_func(_FROM_JSON_ENCODABLE_REGISTRY, type_)


_JSON_ENCODABLE_SUMMARY_REGISTRY: Dict[RegistryKey, ToJSONEncodableCallable] = {}


def register_to_json_encodable_summary(
    *types: RegistryKey,
) -> Callable[[ToJSONEncodableCallable], ToJSONEncodableCallable]:
    """
    Decorator to register a function to convert `type_` to a JSON-encodable summary for
    the UI.
    """
    _validate_registry_keys(*types)

    def _register_to_json_encodable_summary(
        func: ToJSONEncodableCallable,
    ) -> ToJSONEncodableCallable:
        # TODO(@neutralino1): validate func signature
        for type_ in types:
            _JSON_ENCODABLE_SUMMARY_REGISTRY[type_] = func

        return func

    return _register_to_json_encodable_summary


def get_to_json_encodable_summary_func(
    type_: TypeAnnotation,
) -> Optional[ToJSONEncodableCallable]:
    """
    Obtain the serialization function for `type_`.
    """
    validate_type_annotation(type_)
    return _get_registered_func(_JSON_ENCODABLE_SUMMARY_REGISTRY, type_)


# TOOLS


RegisteredFunc = TypeVar("RegisteredFunc")


def _get_registered_func(
    registry: Dict[RegistryKey, RegisteredFunc], type_: TypeAnnotation
) -> Optional[RegisteredFunc]:
    """
    Obtain a registered function (casting, serialization) from a registry.
    """
    validate_type_annotation(type_)
    registry_type = get_origin_type(type_)

    return registry.get(registry_type)


def get_origin_type(type_: TypeAnnotation) -> TypeAnnotation:
    """
    Extract the type by which the casting and serialization logic
    is indexed.

    Typically that is the type, except for type aliases (e.g. `List[int]`)
    where we extract the origin type (e.g. `list`).
    """
    validate_type_annotation(type_)
    registry_type = type_
    if is_parameterized_generic(registry_type) or is_sematic_parametrized_generic_type(
        registry_type
    ):
        registry_type = registry_type.__origin__
    return registry_type


def validate_type_annotation(*types: TypeAnnotation) -> None:
    """Ensure the provided object(s) are ones that Sematic knows how to handle.

    If the type(s) are not valid, raises TypeError.

    Parameters
    ----------
    types:
        The object(s) that may be a type/annotation understood by Sematic.
    """

    def assert_supported(type_):
        try:
            subclasses_type = issubclass(type_, type)
        except TypeError:
            subclasses_type = False
        if type(type_) is type or subclasses_type:
            return
        if not is_parameterized_generic(type_, raise_for_unparameterized=True):
            raise TypeError(
                f"Expected a Sematic-supported type here, but got: {type_}. Please "
                f"refer to the Sematic docs about supported types: "
                f"{_SUPPORTED_TYPES_DOCS}"
            )

    for t in types:
        assert_supported(t)


def is_supported_type_annotation(type_: TypeAnnotation) -> bool:
    """Determine if the provided object is one that Sematic knows how to handle.

    Note that this means "things won't break if it's used," NOT "we have nice
    vizualizations or serialization for it".

    Parameters
    ----------
    types:
        The object(s) that may be a type/annotation understood by Sematic.

    Returns
    -------
    True if the type annotation can be handled by Sematic, False otherwise.
    """
    try:
        validate_type_annotation(type_)
        return True
    except TypeError:
        return False


def is_parameterized_generic(
    type_: TypeAnnotation, raise_for_unparameterized=False
) -> bool:
    """Is this a `typing` type, and if so, is it correctly specified?

    Parameters
    ----------
    type_:
        The 'type' to check for support
    raise_for_unparameterized:
        When this is set to True, will raise a TypeError if the type is found to be
        something that is a generic, but is not yet parameterized
        (e.g. Union without any [...]).

    Returns
    -------
    True if and only if type_ is a generic (i.e. Union or
    Dict) AND it has been parameterized (i.e. Dict[str, int] instead of
    just Dict). Note that in versions of python where certain built-ins
    can act as generics, they will be treated the same as types from
    the typing module.
    """
    is_from_typing = (
        hasattr(type_, "__module__") and getattr(type_, "__module__") == "typing"
    )
    if is_from_typing and type_ in SUPPORTED_GENERIC_TYPING_ANNOTATIONS.keys():
        if raise_for_unparameterized:
            raise TypeError(
                f"{type_} must be parametrized ({type_}[...] " f"instead of {type_})"
            )
        else:
            return False

    # If you call get_origin(Union), it will return None, but
    # get_origin(Union[int, float]) returns Union. Aka, get_origin
    # will only return an origin type if the type is parameterized.
    # that's what we want for these purposes.
    return get_origin(type_) in SUPPORTED_GENERIC_TYPING_ANNOTATIONS.values()


def _is_supported_registry_key(type_: RegistryKey) -> bool:
    try:
        subclasses_type = issubclass(type_, type)
    except TypeError:
        subclasses_type = False
    is_unparameterized_generic = type_ in SUPPORTED_GENERIC_TYPING_ANNOTATIONS.keys()
    return type(type_) is type or subclasses_type or is_unparameterized_generic


def _validate_registry_keys(*types_: RegistryKey):
    for type_ in types_:
        if _is_supported_registry_key(type_):
            continue
        raise TypeError(
            f"Cannot register type {type_}. Please refer to the Sematic docs on "
            f"supported types: "
            f"{_SUPPORTED_TYPES_DOCS}"
        )


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
