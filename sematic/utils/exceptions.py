# Standard Library
import sys
import traceback

# Sematic
from sematic.abstract_calculator import CalculatorError


def format_exception_for_run() -> str:
    """Format an exception trace into a string for usage in a run

    Returns
    -------
    A string showing the stack trace and exception message.
    """
    _, exc, __ = sys.exc_info()
    if isinstance(exc, CalculatorError) and exc.__cause__ is not None:
        # Don't display to the user the parts of the stack from Sematic
        # resolver if the root cause was a failure in Calculator code.
        tb_exception = traceback.TracebackException.from_exception(exc.__cause__)
        return "\n".join(tb_exception.format())
    else:
        return traceback.format_exc()
