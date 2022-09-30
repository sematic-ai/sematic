# Standard Library
from typing import Iterable, List

# Sematic
from sematic import storage
from sematic.abstract_future import FutureState
from sematic.db.models.resolution import ResolutionStatus
from sematic.db.queries import save_resolution, save_run
from sematic.db.tests.fixtures import make_resolution, make_run, test_db  # noqa: F401
from sematic.log_reader import (
    Cursor,
    LogLine,
    LogLineResult,
    _load_inline_logs,
    _load_non_inline_logs,
    get_log_lines_from_line_stream,
    load_log_lines,
    log_prefix,
)
from sematic.resolvers.cloud_resolver import (
    END_INLINE_RUN_INDICATOR,
    START_INLINE_RUN_INDICATOR,
)
from sematic.scheduling.external_job import ExternalJob, JobType
from sematic.tests.fixtures import test_storage  # noqa: F401

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
        log_unavailable_reason=None,
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
        log_unavailable_reason=None,
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
        log_unavailable_reason=None,
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
        log_unavailable_reason=None,
    )


def test_load_non_inline_logs(test_storage, test_db):  # noqa: F811
    run = make_run(future_state=FutureState.RESOLVED)
    save_run(run)

    max_lines = 50
    text_lines = [line.line for line in finite_logs(100)]
    log_file_contents = bytes("\n".join(text_lines), encoding="utf8")
    prefix = log_prefix(run.id, JobType.worker)
    key = f"{prefix}12345.log"

    result = _load_non_inline_logs(
        run_id=run.id,
        still_running=False,
        cursor_file=None,
        cursor_line_index=-1,
        max_lines=max_lines,
        filter_strings=[],
    )
    assert not result.more_after  # run isn't running and there are no logfiles
    assert result.lines == []
    assert result.continuation_cursor is None
    assert result.log_unavailable_reason == "No log files found"
    storage.set(key, log_file_contents)

    result = _load_non_inline_logs(
        run_id=run.id,
        still_running=False,
        cursor_file=None,
        cursor_line_index=-1,
        max_lines=max_lines,
        filter_strings=[],
    )
    cursor = Cursor.from_token(result.continuation_cursor)
    result.continuation_cursor = None
    assert result == LogLineResult(
        continuation_cursor=None,
        more_before=False,
        more_after=True,
        lines=text_lines[:max_lines],
        log_unavailable_reason=None,
    )

    result = _load_non_inline_logs(
        run_id=run.id,
        still_running=False,
        cursor_file=cursor.source_log_key,
        cursor_line_index=cursor.source_file_line_index,
        max_lines=max_lines,
        filter_strings=[],
    )
    cursor = Cursor.from_token(result.continuation_cursor)
    result.continuation_cursor = None
    assert result == LogLineResult(
        continuation_cursor=None,
        more_before=True,
        more_after=True,
        lines=text_lines[max_lines : 2 * max_lines],  # noqa: E203
        log_unavailable_reason=None,
    )

    result = _load_non_inline_logs(
        run_id=run.id,
        still_running=False,
        cursor_file=cursor.source_log_key,
        cursor_line_index=cursor.source_file_line_index,
        max_lines=max_lines,
        filter_strings=[],
    )
    assert result == LogLineResult(
        continuation_cursor=None,
        more_before=True,
        more_after=False,
        lines=[],
        log_unavailable_reason="No matching log lines.",
    )


def test_load_inline_logs(test_storage, test_db):  # noqa: F811
    run = make_run(future_state=FutureState.RESOLVED)
    save_run(run)
    resolution = make_resolution(status=ResolutionStatus.COMPLETE)
    resolution.root_id = run.root_id

    run_text_lines = [line.line for line in finite_logs(100)]
    resolver_lines = ["blah", "blah", "blah"]
    text_lines = (
        resolver_lines
        + [START_INLINE_RUN_INDICATOR.format(run.id)]
        + run_text_lines
        + [END_INLINE_RUN_INDICATOR.format(run.id)]
        + resolver_lines
    )
    max_lines = 50

    log_file_contents = bytes("\n".join(text_lines), encoding="utf8")
    prefix = log_prefix(resolution.root_id, JobType.driver)
    key = f"{prefix}12345.log"

    result = _load_inline_logs(
        run_id=run.id,
        resolution=resolution,
        still_running=False,
        cursor_file=None,
        cursor_line_index=-1,
        max_lines=max_lines,
        filter_strings=[],
    )
    assert not result.more_after  # run isn't alive and resolver logs missing
    assert result.lines == []
    assert result.continuation_cursor is None
    assert result.log_unavailable_reason == "Resolver logs are missing"
    storage.set(key, log_file_contents)

    result = _load_inline_logs(
        run_id=run.id,
        resolution=resolution,
        still_running=False,
        cursor_file=None,
        cursor_line_index=-1,
        max_lines=max_lines,
        filter_strings=[],
    )

    cursor = Cursor.from_token(result.continuation_cursor)
    result.continuation_cursor = None
    assert result == LogLineResult(
        continuation_cursor=None,
        more_before=False,
        more_after=True,
        lines=run_text_lines[:max_lines],
        log_unavailable_reason=None,
    )

    result = _load_inline_logs(
        run_id=run.id,
        resolution=resolution,
        still_running=False,
        cursor_file=cursor.source_log_key,
        cursor_line_index=cursor.source_file_line_index,
        max_lines=max_lines,
        filter_strings=[],
    )
    cursor = Cursor.from_token(result.continuation_cursor)
    result.continuation_cursor = None

    assert result == LogLineResult(
        continuation_cursor=None,
        more_before=True,
        more_after=True,
        lines=run_text_lines[max_lines:],
        log_unavailable_reason=None,
    )

    result = _load_inline_logs(
        run_id=run.id,
        resolution=resolution,
        still_running=False,
        cursor_file=cursor.source_log_key,
        cursor_line_index=cursor.source_file_line_index,
        max_lines=max_lines,
        filter_strings=[],
    )
    result.continuation_cursor = None
    assert result == LogLineResult(
        continuation_cursor=None,
        more_before=True,
        more_after=False,
        lines=[],
        log_unavailable_reason="No matching log lines.",
    )


def test_load_log_lines(test_storage, test_db):  # noqa: F811
    run = make_run(future_state=FutureState.CREATED)
    save_run(run)
    resolution = make_resolution(status=ResolutionStatus.SCHEDULED)
    resolution.root_id = run.root_id
    save_resolution(resolution)
    max_lines = 50

    result = load_log_lines(
        run_id=run.id,
        continuation_cursor=None,
        max_lines=max_lines,
    )
    result.continuation_cursor = None
    assert result == LogLineResult(
        continuation_cursor=None,
        more_before=False,
        more_after=True,
        lines=[],
        log_unavailable_reason="Resolution has not started yet.",
    )

    resolution.status = ResolutionStatus.RUNNING
    save_resolution(resolution)

    result = load_log_lines(
        run_id=run.id,
        continuation_cursor=None,
        max_lines=max_lines,
    )
    result.continuation_cursor = None
    assert result == LogLineResult(
        continuation_cursor=None,
        more_before=False,
        more_after=True,
        lines=[],
        log_unavailable_reason="The run has not yet started executing.",
    )

    run.future_state = FutureState.SCHEDULED
    run.external_jobs = [ExternalJob(kind="fake", try_number=0, external_job_id="fake")]
    save_run(run)
    text_lines = [line.line for line in finite_logs(100)]
    log_file_contents = bytes("\n".join(text_lines), encoding="utf8")
    prefix = log_prefix(run.id, JobType.worker)
    key = f"{prefix}12345.log"
    storage.set(key, log_file_contents)

    result = load_log_lines(
        run_id=run.id,
        continuation_cursor=None,
        max_lines=max_lines,
    )
    token = result.continuation_cursor
    result.continuation_cursor = None
    assert result == LogLineResult(
        continuation_cursor=None,
        more_before=False,
        more_after=True,
        lines=text_lines[:max_lines],
        log_unavailable_reason=None,
    )

    result = load_log_lines(
        run_id=run.id,
        continuation_cursor=token,
        max_lines=max_lines,
    )
    token = result.continuation_cursor
    result.continuation_cursor = None
    assert result == LogLineResult(
        continuation_cursor=None,
        more_before=True,
        more_after=True,
        lines=text_lines[max_lines : 2 * max_lines],  # noqa: E203
        log_unavailable_reason=None,
    )

    result = load_log_lines(
        run_id=run.id,
        continuation_cursor=token,
        max_lines=max_lines,
    )
    token = result.continuation_cursor
    result.continuation_cursor = None
    assert result == LogLineResult(
        continuation_cursor=None,
        more_before=True,
        more_after=True,
        lines=[],
        log_unavailable_reason="No matching log lines.",
    )

    result = load_log_lines(
        run_id=run.id, continuation_cursor=None, max_lines=1, filter_strings=["2", "4"]
    )
    assert result.lines == ["Line 24"]

    result = load_log_lines(
        run_id=run.id,
        continuation_cursor=result.continuation_cursor,
        max_lines=1,
        filter_strings=["2", "4"],
    )
    assert result.lines == ["Line 42"]
