# Standard Library
import distutils.util
from typing import Optional, Union


def str_to_bool(value: Optional[Union[str, bool]]) -> bool:
    """
    Returns a boolean interpretation of the contents of the specified string.
    """
    if isinstance(value, bool):
        return value

    if value is None or len(value) == 0:
        return False

    return bool(distutils.util.strtobool(value))
