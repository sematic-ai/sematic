"""
Datetime lets user display native python datetime object in the UI with specified
formatting
"""
# Standard Library
import typing
from datetime import datetime

# Sematic
from sematic.types.registry import (
    SummaryOutput,
    register_from_json_encodable,
    register_to_json_encodable,
    register_to_json_encodable_summary,
)


@register_to_json_encodable_summary(datetime)
def _datetime_summary(value: datetime, _) -> SummaryOutput:
    return value.isoformat(), {}


@register_to_json_encodable(datetime)
def _datetime_to_encodable(value: datetime, type_: typing.Type[datetime]) -> str:
    return value.isoformat()


@register_from_json_encodable(datetime)
def _datetime_from_encodable(value: str, type_: typing.Type[datetime]) -> datetime:
    return datetime.fromisoformat(value)
