# Standard Library
import distutils.util
from typing import Any, Optional


def as_bool(value: Optional[Any]) -> bool:
    """
    Returns a boolean interpretation of the contents of the specified value.
    """
    if isinstance(value, bool):
        return value

    if value is None:
        return False

    str_value = str(value)
    if len(str_value) == 0:
        return False

    return bool(distutils.util.strtobool(str_value))
