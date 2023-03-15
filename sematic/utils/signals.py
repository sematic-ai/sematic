"""Utility code for dealing with OS signals."""

# Standard Library
from types import FrameType as _FrameType
from typing import Any, Callable, Optional

FrameType = Optional[_FrameType]
HandlerType = Optional[Callable[[int, FrameType], Any]]


def call_signal_handler(
    signal_handler: HandlerType, signum: int, frame: FrameType
) -> Any:
    """Calls the specified signal handler with the specified signal code and frame."""

    if signal_handler is not None and hasattr(signal_handler, "__call__"):
        return signal_handler(signum, frame)
