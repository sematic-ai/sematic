from typing import List, Iterable

from sematic.log_reader import get_log_lines_from_text_stream, load_log_lines, LogLineResult

_streamed_lines: List[str] = []

# Using this should help ensure we're actually properly streaming.
# If anything is attempting to put the whole stream in memory this
# will blow up 💥
def infinite_logs() -> Iterable[str]:
    count = 0
    while True:
        line = f"Line {count}"
        yield line
        count += 1


def finite_logs(n_lines: int) -> Iterable[str]:
    return (f"Line {i}" for i in range(n_lines))


def fake_streamer(to_stream: Iterable[str]) -> Iterable[str]:
    for line in to_stream:
        _streamed_lines.append(line)
        yield line

def test_get_log_lines_from_text_stream_does_streaming():
    _streamed_lines.clear()
    max_lines = 200
    result = get_log_lines_from_text_stream(
        text_stream=fake_streamer(infinite_logs()),
        still_running=True,
        first_line_index=0,
        max_lines=max_lines,
        filter_strings=[],
    )

    assert result == LogLineResult(
        start_index=0,
        end_index=max_lines,
        more_before=False,
        more_after=True,
        lines=[f"Line {i}" for i in range(max_lines)],
        log_unavaiable_reason=None,
    )
    assert _streamed_lines == result.lines

    start_from = 2**20  # Emulate roughly 10 mb of logs
    result = get_log_lines_from_text_stream(
        text_stream=infinite_logs(),
        still_running=True,
        first_line_index=start_from,
        max_lines=max_lines,
        filter_strings=[],
    )

    assert result == LogLineResult(
        start_index=start_from,
        end_index=max_lines + start_from,
        more_before=True,
        more_after=True,
        lines=[f"Line {i}" for i in range(start_from, max_lines + start_from)],
        log_unavaiable_reason=None,
    )

def test_get_log_lines_from_text_stream_more_after():
    max_lines = 200
    kwargs = dict(
        first_line_index=0,
        max_lines=max_lines,
        filter_strings=[],
    )
    result = get_log_lines_from_text_stream(
        text_stream=infinite_logs(),
        still_running=True,
        **kwargs,
    )
    assert result.more_after

    result = get_log_lines_from_text_stream(
        text_stream=finite_logs(max_lines - 1),
        still_running=True,
        **kwargs,
    )
    assert result.more_after

    result = get_log_lines_from_text_stream(
        text_stream=finite_logs(max_lines - 1),
        still_running=False,
        **kwargs,
    )
    assert not result.more_after

def test_get_log_lines_from_text_stream_filter():
    max_lines = 10
    result = get_log_lines_from_text_stream(
        text_stream=fake_streamer(infinite_logs()),
        still_running=True,
        first_line_index=0,
        max_lines=max_lines,
        filter_strings=["2"],
    )

    assert result == LogLineResult(
        start_index=0,
        end_index=max_lines,
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
    prior_result = result

    result = get_log_lines_from_text_stream(
        text_stream=fake_streamer(infinite_logs()),
        still_running=True,
        first_line_index=result.end_index,  # pick up where we left off
        max_lines=max_lines,
        filter_strings=["2"],
    )
    assert result == LogLineResult(
        start_index=prior_result.end_index,
        end_index=max_lines + prior_result.end_index,
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
