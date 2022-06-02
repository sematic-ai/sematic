# Standard library
from typing import Any

# Glow
from glow.types.registry import register_to_json_encodable_summary
from glow.types.serialization import value_to_json_encodable


@register_to_json_encodable_summary(bool)
def _bool_summary(value: bool, _) -> Any:
    return value_to_json_encodable(value, bool)
