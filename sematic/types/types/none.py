# Sematic
from sematic.types.registry import register_to_json_encodable_summary
from sematic.types.serialization import value_to_json_encodable

NoneType = type(None)


# type ignore because mypy says NoneType is of
# type object when it actually is of type type
@register_to_json_encodable_summary(NoneType)  # type: ignore
def _none_summary(value: None, _) -> None:
    return value_to_json_encodable(value, NoneType)
