# Standard Library
import datetime
import enum
import json

# Third-party
import dateutil.parser
from sqlalchemy import inspect, types


class JSONEncodableMixin:
    """
    Base class for all SQLAlchemy models.

    Defines JSON-encodable behavior.
    """

    def to_json_encodable(self):
        return {
            column.key: _to_json_encodable(getattr(self, column.key), column)
            for column in self.__table__.columns
        }

    @classmethod
    def from_json_encodable(cls, json_encodable):
        field_dict = {
            column.key: cls.field_from_json_encodable(column.key, json_encodable)
            for column in inspect(cls).attrs
        }
        return cls(**field_dict)

    @classmethod
    def field_from_json_encodable(cls, field_name, json_encodable):
        return _from_json_encodable(
            json_encodable.get(field_name), getattr(cls, field_name)
        )


JSON_KEY = "json"
ENUM_KEY = "enum"
REDACTED_KEY = "redacted"

REDACTED = "REDACTED"


def _to_json_encodable(value, column):
    info = column.info

    if info.get(REDACTED_KEY, False):
        return REDACTED

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

    if info.get(JSON_KEY, False) and value is not None:
        return json.loads(value)

    return value


def _from_json_encodable(json_encodable, column):
    if json_encodable is None:
        return None

    if isinstance(column.type, types.Enum):
        return getattr(column.type.enum_class, json_encodable)

    if column.info.get(ENUM_KEY, False):
        return getattr(column.info[ENUM_KEY], json_encodable)

    if column.info.get(JSON_KEY, False) and json_encodable is not None:
        return json.dumps(json_encodable)

    if isinstance(column.type, types.DateTime):
        return dateutil.parser.parse(json_encodable)

    return json_encodable
