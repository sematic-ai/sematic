# Standard Library
import dataclasses
import typing

# Sematic
from sematic.types.registry import (
    DataclassKey,
    get_can_cast_func,
    get_safe_cast_func,
    is_valid_typing_alias,
)


# types must be `typing.Any` because `typing` aliases are not type
def can_cast_type(
    from_type: typing.Any, to_type: typing.Any
) -> typing.Tuple[bool, typing.Optional[str]]:
    """
    `can_cast_type` is the main API to verify castability
    of one type into another.

    Types can be Python builtins, aliases and subscribed from
    `typing`, as well as arbitrary classes.

    Parameters
    ----------
    from_type : Any
        Origin type.
    to_type: Any
        Destination type.

    Returns
    -------
    Tuple[bool, Optional[str]]
        A 2-tuple whose first element is whether `from_type` can
        cast to `to_type`, and the second element is a reason
        if the first element is `False`.
    """
    # Should this be `if issubclass(from_type, to_type)`
    # Can instances of subclasses always cast to their parents?
    if from_type is to_type:
        return True, None

    can_cast_func = get_can_cast_func(to_type)

    # If this is a dataclass we fetch the datacalss casting logic
    if can_cast_func is None and dataclasses.is_dataclass(to_type):
        can_cast_func = get_can_cast_func(DataclassKey)

    if can_cast_func is not None:
        return can_cast_func(from_type, to_type)

    # Default behavior
    if issubclass(from_type, to_type):
        return True, None

    return False, "{} cannot cast to {}".format(from_type, to_type)


# type_ must be `typing.Any` because `typing` aliases are not type
def safe_cast(
    value: typing.Any, type_: typing.Any
) -> typing.Tuple[typing.Any, typing.Optional[str]]:
    """
    `safe_cast` is the main API to safely attempt to cast
    a value to a type.

    Parameters
    ----------
    value : Any
        The candidate value to attempt to cast
    type_ : Any
        The target type to attempt to cast value to

    Returns
    -------
    Tuple[Any, Optional[str]]
        A 2-tuple whose first element is the cast value if
        successful or `None`, and the second element is an error message
        if unsuccessful or `None`.
    """
    # 1. First we check if there is a custom casting function
    _safe_cast_func = get_safe_cast_func(type_)

    # 1b. If this is a dataclass we fetch the datacalss casting logic
    if _safe_cast_func is None and dataclasses.is_dataclass(type_):
        _safe_cast_func = get_safe_cast_func(DataclassKey)

    if _safe_cast_func is not None:
        return _safe_cast_func(value, type_)

    # 2. If not, we check if value is simply an instance of type_
    if not is_valid_typing_alias(type_):
        # isinstance is not allowed with generics
        if isinstance(value, type_):
            return value, None

    # 3. Finally we attempt an actual cast
    try:
        return type_(value), None
    except Exception:
        pass

    return None, "Cannot cast {} to {}".format(repr(value), type_)


def cast(value: typing.Any, type_: type) -> typing.Any:
    """
    Similar to `safe_cast` but will raise an exception if
    casting is unsuccessful.

    Parameters
    ----------
    value : Any
        The candidate value to attempt to cast
    type_ : Any
        The target type to attempt to cast value to

    Returns
    -------
    Any
        Cast value

    Raises
    ------
    TypeError
        If the candidate value could not be cast to target type.
    """
    cast_value, error = safe_cast(value, type_)

    if error is not None:
        raise TypeError("Cannot cast {} to {}: {}".format(value, type_.__name__, error))

    return cast_value
