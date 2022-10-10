# Standard Library
import sys
import traceback
from dataclasses import dataclass
from typing import Optional

# Sematic
from sematic.abstract_calculator import CalculatorError


@dataclass
class ExceptionMetadata:
    repr: str
    name: str
    module: str

    @classmethod
    def from_exception(cls, exception: Exception) -> "ExceptionMetadata":
        return ExceptionMetadata(
            repr=str(exception),
            name=exception.__class__.__name__,
            module=exception.__class__.__module__,
        )


def format_exception_for_run(
    exception: Optional[BaseException] = None,
) -> ExceptionMetadata:
    """Format an exception trace into a string for usage in a run

    Returns
    -------
    ExceptionMetadata
    """
    if exception is None:
        _, exception, __ = sys.exc_info()

    repr_, cause_exception = None, exception

    if isinstance(exception, CalculatorError) and exception.__cause__ is not None:
        # Don't display to the user the parts of the stack from Sematic
        # resolver if the root cause was a failure in Calculator code.
        tb_exception = traceback.TracebackException.from_exception(exception.__cause__)
        repr_ = "\n".join(tb_exception.format())
        cause_exception = exception.__cause__
    else:
        repr_ = traceback.format_exc()

    return ExceptionMetadata(
        repr=repr_,
        name=cause_exception.__class__.__name__,
        module=cause_exception.__class__.__module__,
    )
