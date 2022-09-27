# Standard Library
from typing import Iterable, List

# Sematic
from sematic.log_reader import (
    Cursor,
    LogLine,
    LogLineResult,
    get_log_lines_from_line_stream,
)

_streamed_lines: List[str] = []
_DUMMY_LOGS_FILE = "logs.log"
_DUMMY_RUN_ID = "abc123"


# Using this should help ensure we're actually properly streaming.
# If anything is attempting to put the whole stream in memory this
# will blow up
def infinite_logs() -> Iterable[LogLine]:
    count = 0
    while True:
        line = f"Line {count}"
        yield LogLine(source_file=_DUMMY_LOGS_FILE, source_file_index=count, line=line)
        count += 1


def finite_logs(n_lines: int) -> Iterable[LogLine]:
    return (
        LogLine(source_file=_DUMMY_LOGS_FILE, source_file_index=i, line=f"Line {i}")
        for i in range(n_lines)
    )


def fake_streamer(to_stream: Iterable[LogLine]) -> Iterable[LogLine]:
    for line in to_stream:
        _streamed_lines.append(line.line)
        yield line


def test_get_log_lines_from_line_stream_does_streaming():
    _streamed_lines.clear()
    max_lines = 200
    result = get_log_lines_from_line_stream(
        line_stream=fake_streamer(infinite_logs()),
        still_running=True,
        cursor_source_file=None,
        cursor_line_index=-1,
        max_lines=max_lines,
        filter_strings=[],
        run_id=_DUMMY_RUN_ID,
    )
    cursor = Cursor.from_token(result.continuation_cursor)
    result.continuation_cursor = None

    assert result == LogLineResult(
        continuation_cursor=None,
        more_before=False,
        more_after=True,
        lines=[f"Line {i}" for i in range(max_lines)],
        log_unavaiable_reason=None,
    )
    assert _streamed_lines == result.lines

    # emulate continuation
    result = get_log_lines_from_line_stream(
        line_stream=infinite_logs(),
        still_running=True,
        cursor_source_file=cursor.source_log_key,
        cursor_line_index=cursor.source_file_line_index,
        max_lines=max_lines,
        filter_strings=[],
        run_id=_DUMMY_RUN_ID,
    )
    cursor = Cursor.from_token(result.continuation_cursor)
    result.continuation_cursor = None

    assert result == LogLineResult(
        continuation_cursor=None,
        more_before=True,
        more_after=True,
        lines=[f"Line {i}" for i in range(max_lines, 2 * max_lines)],
        log_unavaiable_reason=None,
    )


def test_get_log_lines_from_line_stream_more_after():
    max_lines = 200
    kwargs = dict(
        cursor_source_file=None,
        cursor_line_index=-1,
        max_lines=max_lines,
        filter_strings=[],
        run_id=_DUMMY_RUN_ID,
    )
    result = get_log_lines_from_line_stream(
        line_stream=infinite_logs(),
        still_running=True,
        **kwargs,
    )
    assert result.more_after

    result = get_log_lines_from_line_stream(
        line_stream=finite_logs(max_lines - 1),
        still_running=True,
        **kwargs,
    )
    assert result.more_after

    result = get_log_lines_from_line_stream(
        line_stream=finite_logs(max_lines - 1),
        still_running=False,
        **kwargs,
    )
    assert not result.more_after


def test_get_log_lines_from_line_stream_filter():
    max_lines = 10
    result = get_log_lines_from_line_stream(
        line_stream=fake_streamer(infinite_logs()),
        still_running=True,
        cursor_source_file=None,
        cursor_line_index=-1,
        run_id=_DUMMY_RUN_ID,
        max_lines=max_lines,
        filter_strings=["2"],
    )
    cursor = Cursor.from_token(result.continuation_cursor)
    result.continuation_cursor = None

    assert result == LogLineResult(
        continuation_cursor=None,
        more_before=False,
        more_after=True,
        lines=[
            "Line 2",
            "Line 12",
            "Line 20",
            "Line 21",
            "Line 22",
            "Line 23",
            "Line 24",
            "Line 25",
            "Line 26",
            "Line 27",
        ],
        log_unavaiable_reason=None,
    )

    result = get_log_lines_from_line_stream(
        line_stream=fake_streamer(infinite_logs()),
        still_running=True,
        cursor_source_file=cursor.source_log_key,
        cursor_line_index=cursor.source_file_line_index,
        run_id=_DUMMY_RUN_ID,
        max_lines=max_lines,
        filter_strings=["2"],
    )
    cursor = Cursor.from_token(result.continuation_cursor)
    result.continuation_cursor = None
    assert result == LogLineResult(
        continuation_cursor=None,
        more_before=True,
        more_after=True,
        lines=[
            "Line 28",
            "Line 29",
            "Line 32",
            "Line 42",
            "Line 52",
            "Line 62",
            "Line 72",
            "Line 82",
            "Line 92",
            "Line 102",
        ],
        log_unavaiable_reason=None,
    )
