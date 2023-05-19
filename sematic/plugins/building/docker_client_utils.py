"""
Utility code for interacting with the `docker-py` client.
"""
# Standard Library
import sys
import textwrap
from typing import Any, Dict, Generator, List, Optional, TextIO

_ROLLING_PRINT_COLUMNS = 120
_ROLLING_PRINT_ROWS = 10


def _rolling_print_status_updates(
    status_updates: Generator[Dict[str, Any], None, None],
    output_handle: TextIO = sys.stderr,
    columns: int = _ROLLING_PRINT_COLUMNS,
    rows: int = _ROLLING_PRINT_ROWS,
) -> Optional[Dict[str, Any]]:
    """
    Prints a rolling window of Docker server status message updates.
    """
    message_window: List[str] = []

    for status_update in status_updates:

        if "error" in status_update.keys():
            return status_update

        update_str = _docker_status_update_to_str(status_update)
        if update_str is None:
            continue

        line_count = len(message_window)
        for raw_line in update_str.split("\n"):
            wrapped_lines = textwrap.wrap(
                raw_line, replace_whitespace=False, width=columns
            )
            message_window += wrapped_lines

        if len(message_window) <= rows:
            for message in message_window[line_count:]:
                print(message, file=output_handle)

        else:
            message_window = message_window[-rows:]
            message_window[0] = "[...]"

            print(f"\033[{line_count + 1}F", file=output_handle)
            for message in message_window:
                print(f"\033[K{message}", file=output_handle)

    return None


def _docker_status_update_to_str(status_update: Dict[str, Any]) -> Optional[str]:
    """
    Returns a textual representation of the status update dict received from the Docker
    server, or None if it was devoid of useful information.
    """
    length = len(status_update)

    if length == 0:
        return None

    if length == 1:
        k, v = next(iter(status_update.items()))
        if v is None or len(str(v).strip()) == 0:
            # only one key with an empty value
            return None
        return str(v).strip()

    return " ".join([str(v).strip() for _, v in sorted(status_update.items())])
