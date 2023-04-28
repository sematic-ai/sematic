"""
Module containing testing utility code.
"""
# Standard Library
import os
from typing import Any


def assert_logs_captured(caplog: Any, *messages: str) -> None:
    """
    Asserts that the specified messages have been captured in the pytest capture log.

    Example
    -------
    # caplog is a stock fixture; no import necessary
    def test_capture(caplog):
        with caplog.at_level(logging.DEBUG):
            def my_function():
                logger.info("Expected log line")
            my_function()
            assert_logs_captured(caplog, "Expected log line")

    Raises
    ------
    AssertionError:
        If one or more of the specified messages were not found in the captured log lines.

    Parameters
    ----------
    caplog: Callable[[], Any]
        The pytest caplog.
    messages: List[str]
        The potentially partial messages to check for in the captured logs.
    """
    log_lines = {rec.message for rec in caplog.records}

    for message in messages:
        found = False

        for log_line in log_lines:
            if message in log_line:
                found = True

        if not found:
            raise AssertionError(
                f"Message {message} not found in captured log lines: {log_lines}"
            )


RUN_SLOW_TESTS = "RUN_SLOW_TESTS" in os.environ
