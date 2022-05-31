# Glow
from glow.types.registry import register_to_json_encodable_summary
from glow.types.serialization import value_to_json_encodable

NoneType = type(None)


@register_to_json_encodable_summary(NoneType)
def _none_summary(value: None, _) -> None:
    return value_to_json_encodable(value, NoneType)
