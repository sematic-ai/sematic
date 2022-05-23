# Glow
import copy
import typing
from glow.types.registry import DataclassKey, register_safe_cast
from glow.types.casting import safe_cast


@register_safe_cast(DataclassKey)
def _safe_cast_dataframe(
    value: typing.Any, type_: typing.Any
) -> typing.Tuple[typing.Any, typing.Optional[str]]:
    """
    Casting logic for dataclasses.
    """
    cast_value = copy.deepcopy(value)

    for name, field in type_.__dataclass_fields__.items():
        field_value = getattr(value, name)
        cast_field, error = safe_cast(field_value, field.type)
        if error is not None:
            return None, "Cannot cast {} to {}: {}".format(value, type_, error)

        setattr(cast_value, name, cast_field)

    return cast_value, None
