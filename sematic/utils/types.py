# Standard Library
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

    return bool(strtobool(str_value))


# Implementation of strtobool from: https://github.com/drgarcia1986/simple-settings
_MAP = {
    "y": True,
    "yes": True,
    "t": True,
    "true": True,
    "on": True,
    "1": True,
    "n": False,
    "no": False,
    "f": False,
    "false": False,
    "off": False,
    "0": False,
}


def strtobool(value):
    try:
        return _MAP[str(value).lower()]
    except KeyError:
        raise ValueError('"{}" is not a valid bool value'.format(value))
