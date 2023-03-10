# Sematic
from sematic.types.registry import SummaryOutput, register_to_json_encodable_summary
from sematic.types.serialization import value_to_json_encodable


@register_to_json_encodable_summary(bool)
def _bool_summary(value: bool, _) -> SummaryOutput:
    return value_to_json_encodable(value, bool), {}
