# Standard Library
import copy
import dataclasses
from typing import (
    Any,
    Callable,
    Dict,
    Literal,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
    get_args,
    get_origin,
)

# Sematic
from sematic.types.casting import can_cast_type, safe_cast
from sematic.types.registry import (
    DataclassKey,
    SummaryOutput,
    is_parameterized_generic,
    register_can_cast,
    register_from_json_encodable,
    register_safe_cast,
    register_to_json_encodable,
    register_to_json_encodable_summary,
)
from sematic.types.serialization import (
    get_json_encodable_summary,
    type_from_json_encodable,
    type_to_json_encodable,
    value_from_json_encodable,
    value_to_json_encodable,
)


@register_safe_cast(DataclassKey)
def _safe_cast_dataclass(value: Any, type_: Any) -> Tuple[Any, Optional[str]]:
    """
    Casting logic for dataclasses.

    converts dicts to type_
    if value is an instance of a subclass of type_, class is conserved.
    """

    # If value is an instance of type_ or of a subclass of type_
    # we want to make sure we conserve the subclass
    # Otherwise we will create an instance of type_, and we use a
    # dict to prepare parameters.
    create_instance_from_scratch = not isinstance(value, type_)

    if create_instance_from_scratch:
        cast_value = dict()
    else:
        # Otherwise we make sure the subclass is conserved, including
        # potential additional fields.
        cast_value = copy.deepcopy(value)

    for name, field in type_.__dataclass_fields__.items():
        try:
            # First we attempt to access the property
            field_value = getattr(value, name)
        except AttributeError:
            try:
                # Maybe it's a dictionary
                field_value = value[name]
            except (TypeError, KeyError):
                return None, "Cannot cast {} to {}: Field {} is missing".format(
                    repr(value), type_, repr(name)
                )

        cast_field, error = safe_cast(field_value, field.type)
        if error is not None:
            return None, "Cannot cast field '{}' of {} to {}: {}".format(
                name, repr(value), type_, error
            )

        if create_instance_from_scratch:
            cast_value[name] = cast_field
        else:
            try:
                setattr(cast_value, name, cast_field)
            except dataclasses.FrozenInstanceError:
                # it's frozen, and the casts all passed, so we're fine
                # to just leave the object as-is.
                pass

    if create_instance_from_scratch:
        cast_value = type_(**cast_value)

    return cast_value, None


@register_can_cast(DataclassKey)
def _can_cast_to_dataclass(from_type: Any, to_type: Any) -> Tuple[bool, Optional[str]]:
    prefix = "Cannot cast {} to {}".format(from_type, to_type)

    if not dataclasses.is_dataclass(from_type):
        return False, "{}: not a dataclass".format(prefix)

    from_fields: Dict[str, dataclasses.Field] = from_type.__dataclass_fields__
    to_fields: Dict[str, dataclasses.Field] = to_type.__dataclass_fields__

    missing_fields = to_fields.keys() - from_fields.keys()
    if len(missing_fields) > 0:
        return False, "{}: missing fields: {}".format(prefix, repr(missing_fields))

    for name, field in to_fields.items():
        can_cast, error = can_cast_type(from_fields[name].type, field.type)
        if not can_cast:
            return False, "{}: field {} cannot cast: {}".format(
                prefix, repr(name), error
            )

    return True, None


@register_to_json_encodable(DataclassKey)
def _dataclass_to_json_encodable(value: Any, type_: Any) -> Any:
    if value is None:
        raise ValueError(f"Expected {type_}, got None")
    return _serialize_dataclass(
        lambda v, t: (value_to_json_encodable(v, t), {}), value, type_
    )[0]


@register_from_json_encodable(DataclassKey)
def _dataclass_from_json_encodable(value: Any, type_: Any) -> Any:
    types = value["types"]
    values = value["values"]
    root_type_json = value["root_type"]
    root_type = type_from_json_encodable(root_type_json)
    if not issubclass(root_type, type_):
        raise TypeError(
            f"Serialized value was a {root_type}, "
            f"could not deserialize to a {type_}"
        )

    kwargs = {}

    fields: Dict[str, dataclasses.Field] = root_type.__dataclass_fields__

    for name, field in fields.items():
        field_type = field.type
        if name in types:
            field_type = type_from_json_encodable(types[name])

        if name in values:
            # if the values were written with an older version of
            # the dataclass, there may not be a value for certain
            # fields. In such cases, we will rely on the defaults
            # in the dataclass constructor.
            kwargs[name] = value_from_json_encodable(values[name], field_type)

    return root_type(**kwargs)


@register_to_json_encodable_summary(DataclassKey)
def _dataclass_to_json_encodable_summary(value: Any, type_: Any) -> SummaryOutput:
    return _serialize_dataclass(get_json_encodable_summary, value, type_)


def _serialize_dataclass(serializer: Callable, value: Any, _) -> SummaryOutput:
    # We use type(value) instead of the passed type because we want to
    # conserve any subclasses
    type_ = type(value)

    output: Dict[
        Union[Literal["values"], Literal["types"], Literal["root_type"]],
        Dict[str, Any],
    ] = {"values": {}, "types": {}, "root_type": type_to_json_encodable(type_)}

    fields: Dict[str, dataclasses.Field] = type_.__dataclass_fields__

    blobs: Dict[str, bytes] = {}

    for name, field in fields.items():
        field_value = getattr(value, name)

        # The actual value type can be different from the field type if
        # the value is an instance of a subclass
        value_type = type(field_value)
        field_type = value_serialization_type = field.type

        # Only if the value type is different (e.g. subclass) do we persist the type
        # serialization
        # `typing` generics are excluded as they will always be different since the type
        # parametrization (e.g. `int` for `List[int]`) is not conserved on
        # instances
        if not (value_type is field_type) and not is_parameterized_generic(field_type):
            output["types"][name] = type_to_json_encodable(value_type)
            value_serialization_type = value_type

        output["values"][name], blobs_ = serializer(
            field_value, value_serialization_type
        )
        blobs.update(blobs_)

    return output, blobs


T = TypeVar("T")


def fromdict(dataclass_type: Type[T], as_dict: Dict[str, Any]) -> T:
    """Invert dataclasses.asdict for simple dataclass structures.

    This will only work assuming the following conditions are met:
    - all fields of the provided class are primitives, a supported collection,
      or a dataclass
    - the dict was serialized from an instance of the dataclass type, not a subclass
      of it or an entirely different class
    - the dataclass uses the autogenerated __init__, or has all fields as valid
      keyword args to its __init__.
    - All fields have type declarations, with Dict and List fields specifying
      their key/value types in the type annotation.

    Supported collections include:
    - lists where the element type is a primitive or another dataclass type
      that would be a valid input to from_dict
    - dicts where the value type is a primitive or another dataclass type
      that would be a valid input to from_dict

    Because it leverages these simplifying assumptions, the serializations
    supported by this function can be more compact than those for standard
    Sematic dataclass serializations (which support a broader range of types).

    Parameters
    ----------
    dataclass_type:
        A Dataclass type that the dict should be deserialized into
    as_dict:
        The dataclass serialized in the format produced by dataclasses.asdict

    Returns
    -------
    An instance of dataclass_type.
    """
    if not dataclasses.is_dataclass(dataclass_type):
        raise TypeError(
            f"as_dict can only be called with dataclass types. Got: {dataclass_type}"
        )
    kwargs = {}
    for field in dataclasses.fields(dataclass_type):  # type: ignore
        name = field.name
        if name not in as_dict:
            continue
        if not field.init:
            continue
        dict_value = as_dict[name]
        if dataclasses.is_dataclass(field.type):
            kwargs[name] = fromdict(field.type, dict_value)
            continue
        if get_origin(field.type) == list:
            element_type = get_args(field.type)[0]
            if dataclasses.is_dataclass(element_type):
                kwargs[name] = [
                    fromdict(element_type, element) for element in dict_value
                ]
                continue
        if get_origin(field.type) == dict:
            value_type = get_args(field.type)[1]
            if dataclasses.is_dataclass(value_type):
                kwargs[name] = {
                    key: fromdict(value_type, value)
                    for key, value in dict_value.items()
                }
                continue
        kwargs[name] = dict_value

    return dataclass_type(**kwargs)
