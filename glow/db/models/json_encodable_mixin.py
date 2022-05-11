# Standard library
import base64
import datetime
import enum


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


def _to_json_encodable(value, column):
    HEX_ENCODE = "hex_encode"

    info = column.info
    if isinstance(value, bytes):
        if info.get(HEX_ENCODE, False):
            return value.hex()
        else:
            return base64.b64encode(value).decode("ascii")

    if isinstance(value, datetime.datetime):
        return value.isoformat()

    if isinstance(value, enum.Enum):
        return value.value

    return value
