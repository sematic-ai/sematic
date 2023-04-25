# Standard Library
import signal
from contextlib import contextmanager
from typing import Optional

# Sematic
from sematic.utils.exceptions import TimeoutError


@contextmanager
def timeout(duration_seconds: Optional[int]):
    """Execute the contents of the function in less than duration_seconds or raise error.

    Uses signal.alarm to trigger the timeout, which requires that no alarm must be in use
    at the time this one is set (signal.alarm only supports one alarm at a time). This
    context manager must also be called from code executing on the program's main thread.

    Parameters
    ----------
    duration_seconds:
        The amount of time the code has to complete. Must be a positive integer or None.
        If None, the code may take as long as required to complete.
    """
    if duration_seconds is None:
        yield
        return

    if duration_seconds != int(duration_seconds):
        # this is required by signal.alarm
        raise ValueError(
            f"Timeout duration must be an integer, got: {duration_seconds}"
        )
    if duration_seconds <= 0:
        raise ValueError(f"Timeout duration must be positive, got: {duration_seconds}")

    def new_handler(signal_number, frame):
        raise TimeoutError(f"Code did not complete execution in {duration_seconds}s.")

    original_handler = signal.signal(signal.SIGALRM, new_handler)

    if original_handler not in {None, signal.SIG_IGN, signal.SIG_DFL}:
        raise RuntimeError(
            f"Cannot set timeout, as a signal handler was already "
            f"set for SIGALRM: {original_handler}"
        )

    signal.alarm(duration_seconds)
    try:
        yield
    finally:
        # this disables the alarm
        signal.alarm(0)
        signal.signal(signal.SIGALRM, signal.SIG_DFL)
