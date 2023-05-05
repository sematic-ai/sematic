# Standard Library
import dataclasses
import datetime
import enum
import json
from typing import Any

# Third-party
import dateutil.parser
from sqlalchemy import Column, inspect, types


class JSONEncodableMixin:
    """
    Base class for all SQLAlchemy models.

    Defines JSON-encodable behavior.
    """

    def to_json_encodable(self, redact: bool = True):
        return {
            column.key: _to_json_encodable(getattr(self, column.key), column)
            for column in self.__table__.columns  # type: ignore
            if (not column.info.get(REDACTED_KEY, False) or not redact)
        }

    @classmethod
    def from_json_encodable(cls, json_encodable):
        field_dict = {
            column.key: cls.field_from_json_encodable(column, json_encodable)
            for column in inspect(cls).attrs
            if column.key in json_encodable
            or column.info.get(ALIAS_KEY) in json_encodable
        }
        return cls(**field_dict)

    @classmethod
    def field_from_json_encodable(cls, column: Column, json_encodable):
        field_name = column.key
        field_alias = column.info.get(
            ALIAS_KEY,
            column.key,
        )
        payload_key = field_name
        if field_name not in json_encodable and field_alias in json_encodable:
            payload_key = field_alias

        return _from_json_encodable(
            json_encodable[payload_key],
            getattr(cls, field_name),  # type: ignore
        )


JSON_KEY = "json"
ENUM_KEY = "enum"
REDACTED_KEY = "redacted"
ALIAS_KEY = "alias"


def _to_json_encodable(value: Any, column: Column) -> Any:
    info = column.info

    if isinstance(value, datetime.datetime):
        # SQLite does not store timezone
        utc_value = datetime.datetime(
            value.year,
            value.month,
            value.day,
            value.hour,
            value.minute,
            value.second,
            value.microsecond,
            tzinfo=datetime.timezone.utc,
        )
        return utc_value.isoformat()

    if isinstance(value, enum.Enum):
        return value.value

    if dataclasses.is_dataclass(value):
        return dataclasses.asdict(value)

    if info.get(JSON_KEY, False) and value is not None:
        return json.loads(value)

    return value


def _from_json_encodable(json_encodable: Any, column: Column) -> Any:
    if json_encodable is None:
        return None

    if isinstance(column.type, types.Enum):
        return getattr(column.type.enum_class, json_encodable)  # type: ignore

    if column.info.get(ENUM_KEY, False):
        return getattr(column.info[ENUM_KEY], json_encodable)

    if column.info.get(JSON_KEY, False) and json_encodable is not None:
        return json.dumps(json_encodable)

    if isinstance(column.type, types.DateTime):
        return dateutil.parser.parse(json_encodable)

    return json_encodable
