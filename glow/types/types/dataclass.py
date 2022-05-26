# Standard library
import copy
import typing
import dataclasses

# Glow
from glow.types.registry import (
    DataclassKey,
    is_valid_typing_alias,
    register_can_cast,
    register_safe_cast,
    register_to_json_encodable,
)
from glow.types.casting import can_cast_type, safe_cast
from glow.types.serialization import type_to_json_encodable, value_to_json_encodable


@register_safe_cast(DataclassKey)
def _safe_cast_dataclass(
    value: typing.Any, type_: typing.Any
) -> typing.Tuple[typing.Any, typing.Optional[str]]:
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
            return None, "Cannot cast {} to {}: {}".format(repr(value), type_, error)

        if create_instance_from_scratch:
            cast_value[name] = cast_field
        else:
            setattr(cast_value, name, cast_field)

    if create_instance_from_scratch:
        cast_value = type_(**cast_value)

    return cast_value, None


@register_can_cast(DataclassKey)
def _can_cast_to_dataclass(
    from_type: typing.Any, to_type: typing.Any
) -> typing.Tuple[bool, typing.Optional[str]]:
    prefix = "Cannot cast {} to {}".format(from_type, to_type)

    if not dataclasses.is_dataclass(from_type):
        return False, "{}: not a dataclass".format(prefix)

    from_fields: typing.Dict[str, dataclasses.Field] = from_type.__dataclass_fields__
    to_fields: typing.Dict[str, dataclasses.Field] = to_type.__dataclass_fields__

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
def _dataclass_to_json_encodable(value: typing.Any, _) -> typing.Any:
    # We use type(value) instead of the passed type because we want to
    # conserve any subclasses
    type_ = type(value)

    output: typing.Dict[
        typing.Union[typing.Literal["values"], typing.Literal["types"]],
        typing.Dict[str, typing.Any],
    ] = {"values": {}, "types": {}}

    fields: typing.Dict[str, dataclasses.Field] = type_.__dataclass_fields__

    for name, field in fields.items():
        field_value = getattr(value, name)

        # The actual value type can be different from the field type if
        # the value is an instance of a subclass
        value_type = type(field_value)
        field_type = value_serialization_type = field.type

        # Only if the value type is different (e.g. subclass) do we persist the type
        # serialization
        # `typing` generics are excluded as they will always be different since the type
        # parametrization (e.g. `int` for `typing.List[int]`) is not conserved on
        # instances
        if not (value_type is field_type) and not is_valid_typing_alias(field_type):
            output["types"][name] = type_to_json_encodable(value_type)
            value_serialization_type = value_type

        output["values"][name] = value_to_json_encodable(
            field_value, value_serialization_type
        )

    return output
