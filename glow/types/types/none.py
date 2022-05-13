# Standard library
import typing

# Glow
from glow.types.registry import register_can_cast, register_safe_cast


@register_can_cast(type(None))
def can_cast_type(type_: type, _) -> typing.Tuple[bool, typing.Optional[str]]:
    if type_ is type(None):  # noqa: E721
        # Adding type: ignore here because for some reason mypy
        # sees None as incompatible with Optional[str] :shrug:
        # @neutralino1
        return True, None  # type: ignore

    return False, "Cannot cast {} to NoneType".format(type_)


@register_safe_cast(type(None))
def safe_cast(value: typing.Any, _) -> typing.Tuple[typing.Any, typing.Optional[str]]:
    if value is None:
        return value, None

    return None, "{} is not None".format(repr(value))
