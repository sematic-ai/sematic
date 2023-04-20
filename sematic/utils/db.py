# Standard Library
import enum
from typing import Type

# Third-party
from sqlalchemy.types import Integer, TypeDecorator


class IntEnum(TypeDecorator):
    """
    As seen on https://michaelcho.me/article/using-python-enums-in-sqlalchemy-models
    Enables passing in a Python enum and storing the enum's *value* in the db.
    The default would have stored the enum's *name* (ie the string).
    """

    impl = Integer

    cache_ok = True

    def __init__(self, enumtype: Type[enum.IntEnum], *args, **kwargs):
        super(IntEnum, self).__init__(*args, **kwargs)
        self._enumtype = enumtype

    def process_bind_param(self, value, dialect):
        if isinstance(value, int):
            return value

        return value.value

    def process_result_value(self, value, dialect):
        return self._enumtype(value)
