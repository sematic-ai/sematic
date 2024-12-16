"""
Utility code for interacting with the `docker-py` client.
"""

# Standard Library
import logging
import sys
import textwrap
from typing import Any, Dict, Generator, List, Optional, TextIO


logger = logging.getLogger(__name__)

_ROLLING_PRINT_COLUMNS = 120
_ROLLING_PRINT_ROWS = 10


def rolling_print_status_updates(
    status_updates: Generator[Dict[str, Any], None, None],
    output_handle: Optional[TextIO] = None,
    columns: int = _ROLLING_PRINT_COLUMNS,
    rows: int = _ROLLING_PRINT_ROWS,
) -> Optional[Dict[str, Any]]:
    """
    Prints a rolling window of Docker server status message updates.

    This behavior is deactivated if the logging level is `DEBUG`, in which case all the
    messages are kept.
    """
    output_handle = output_handle or sys.stderr
    message_window: List[str] = []
    debugging = logger.isEnabledFor(logging.DEBUG)

    for status_update in status_updates:
        if "error" in status_update.keys():
            return status_update

        update_str = _docker_status_update_to_str(status_update)
        if update_str is None:
            continue

        if debugging:
            # disable the rolling window
            print(update_str, file=output_handle)
            continue

        # wrap the new status messages and add them to the rolling window
        previous_line_count = len(message_window)
        for raw_line in update_str.split("\n"):
            wrapped_lines = textwrap.wrap(
                raw_line, replace_whitespace=False, width=columns
            )
            message_window += wrapped_lines

        # if we don't need to roll the window, then we haven't ever done it; just print
        if len(message_window) <= rows:
            for message in message_window[previous_line_count:]:
                print(message, file=output_handle)

        # we need to roll the window by discarding from the beginning of it,
        # then printing over the previously-printed text
        else:
            message_window = message_window[-rows:]
            message_window[0] = "[...]"

            # 033[F -> go up
            print(f"\033[{previous_line_count + 1}F", file=output_handle)
            for message in message_window:
                # \033[K -> clear line
                print(f"\033[K{message}", file=output_handle)

    return None


def _docker_status_update_to_str(status_update: Dict[str, Any]) -> Optional[str]:
    """
    Returns a textual representation of the status update dict received from the Docker
    server, or None if it was devoid of useful information.
    """
    if len(status_update) == 0:
        return None

    values = []

    # always present the values in the same order
    # (by their keys, even if the keys are not included in the message update)
    for _, v in sorted(status_update.items()):
        # skip falsy values, such as empty dicts
        if v:
            str_val = str(v).strip()
            if len(str_val) > 0:
                values.append(str_val)

    if len(values) == 0:
        return None

    return " ".join(values)
