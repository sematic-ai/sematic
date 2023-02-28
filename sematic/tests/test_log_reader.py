# Standard Library
from typing import Iterable, List

# Third-party
import pytest

# Sematic
from sematic.abstract_future import FutureState
from sematic.api.tests.fixtures import mock_storage  # noqa: F401
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
    line_stream_from_log_directory,
    load_log_lines,
    log_prefix,
    v1_log_prefix,
)
from sematic.resolvers.cloud_resolver import (
    END_INLINE_RUN_INDICATOR,
    START_INLINE_RUN_INDICATOR,
)
from sematic.scheduling.external_job import ExternalJob, JobType

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
        cursor_had_more_before=False,
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
        log_info_message=None,
    )
    assert _streamed_lines == result.lines

    # emulate continuation
    result = get_log_lines_from_line_stream(
        line_stream=infinite_logs(),
        still_running=True,
        cursor_source_file=cursor.source_log_key,
        cursor_line_index=cursor.source_file_line_index,
        cursor_had_more_before=cursor.traversal_had_lines,
        max_lines=max_lines,
        filter_strings=[],
        run_id=_DUMMY_RUN_ID,
    )
    result.continuation_cursor = None

    assert result == LogLineResult(
        continuation_cursor=None,
        more_before=True,
        more_after=True,
        lines=[f"Line {i}" for i in range(max_lines, 2 * max_lines)],
        log_info_message=None,
    )


def test_get_log_lines_from_line_stream_more_after():
    max_lines = 200
    kwargs = dict(
        cursor_source_file=None,
        cursor_line_index=-1,
        cursor_had_more_before=False,
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
        cursor_had_more_before=False,
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
        log_info_message=None,
    )

    result = get_log_lines_from_line_stream(
        line_stream=fake_streamer(infinite_logs()),
        still_running=True,
        cursor_source_file=cursor.source_log_key,
        cursor_line_index=cursor.source_file_line_index,
        cursor_had_more_before=cursor.traversal_had_lines,
        run_id=_DUMMY_RUN_ID,
        max_lines=max_lines,
        filter_strings=["2"],
    )

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
        log_info_message=None,
    )


def prepare_logs_v1(run_id, text_lines, mock_storage, job_type):  # noqa: F811
    log_file_contents = bytes("\n".join(text_lines), encoding="utf8")
    prefix = v1_log_prefix(run_id, job_type)
    key = f"{prefix}12345.log"
    mock_storage.set(key, log_file_contents)
    return prefix


def prepare_logs_v2(
    run_id,
    text_lines,
    mock_storage,  # noqa: F811
    job_type,
    break_at_line=52,
    emulate_pending_more_lines=False,
):
    lines_part_1 = text_lines[:break_at_line]
    lines_part_2 = text_lines[break_at_line:]

    log_file_contents_part_1 = bytes("\n".join(lines_part_1), encoding="utf8")
    prefix = log_prefix(run_id, job_type)
    key_part_1 = f"{prefix}12345.log"
    mock_storage.set(key_part_1, log_file_contents_part_1)

    if emulate_pending_more_lines:
        # act as if the second file hasn't been produced yet
        return prefix
    log_file_contents_part_2 = bytes("\n".join(lines_part_2), encoding="utf8")
    prefix = log_prefix(run_id, job_type)
    key_part_2 = f"{prefix}12346.log"
    mock_storage.set(key_part_2, log_file_contents_part_2)
    return prefix


@pytest.mark.parametrize(
    "log_preparation_function",
    (
        prepare_logs_v1,
        prepare_logs_v2,
    ),
)
def test_load_non_inline_logs(
    test_db, mock_storage, log_preparation_function  # noqa: F811
):
    run = make_run(future_state=FutureState.RESOLVED)
    save_run(run)

    max_lines = 50
    text_lines = [line.line for line in finite_logs(100)]

    result = _load_non_inline_logs(
        run_id=run.id,
        still_running=False,
        cursor_file=None,
        cursor_line_index=-1,
        cursor_had_more_before=False,
        max_lines=max_lines,
        filter_strings=[],
    )
    assert not result.more_after  # run isn't running and there are no logfiles
    assert result.lines == []
    assert result.continuation_cursor is None
    assert result.log_info_message == "No log files found"
    log_preparation_function(run.id, text_lines, mock_storage, JobType.worker)

    result = _load_non_inline_logs(
        run_id=run.id,
        still_running=False,
        cursor_file=None,
        cursor_line_index=-1,
        cursor_had_more_before=False,
        max_lines=max_lines,
        filter_strings=[],
    )
    assert result.continuation_cursor is not None
    cursor = Cursor.from_token(result.continuation_cursor)
    assert cursor.traversal_had_lines
    result.continuation_cursor = None
    assert result == LogLineResult(
        continuation_cursor=None,
        more_before=False,
        more_after=True,
        lines=text_lines[:max_lines],
        log_info_message=None,
    )

    result = _load_non_inline_logs(
        run_id=run.id,
        still_running=False,
        cursor_file=cursor.source_log_key,
        cursor_line_index=cursor.source_file_line_index,
        cursor_had_more_before=cursor.traversal_had_lines,
        max_lines=max_lines,
        filter_strings=[],
    )
    assert result.continuation_cursor is not None
    cursor = Cursor.from_token(result.continuation_cursor)
    result.continuation_cursor = None
    assert result == LogLineResult(
        continuation_cursor=None,
        more_before=True,
        more_after=True,
        lines=text_lines[max_lines : 2 * max_lines],  # noqa: E203
        log_info_message=None,
    )

    result = _load_non_inline_logs(
        run_id=run.id,
        still_running=False,
        cursor_file=cursor.source_log_key,
        cursor_line_index=cursor.source_file_line_index,
        cursor_had_more_before=cursor.traversal_had_lines,
        max_lines=max_lines,
        filter_strings=[],
    )
    assert result == LogLineResult(
        continuation_cursor=None,
        more_before=True,
        more_after=False,
        lines=[],
        log_info_message="No matching log lines.",
    )


def test_line_stream_from_log_directory(mock_storage, test_db):  # noqa: F811
    run = make_run(future_state=FutureState.RESOLVED)
    save_run(run)
    n_lines = 500
    text_lines = [f"Line {i}" for i in range(n_lines)]
    prefix = prepare_logs_v2(
        run_id=run.id,
        text_lines=text_lines,
        mock_storage=mock_storage,
        job_type=JobType.worker,
    )
    line_stream = line_stream_from_log_directory(prefix, None, None)
    materialized_line_stream = list(line_stream)
    with pytest.raises(StopIteration):
        # if it was a generator as expected, we exhausted it when we materialized it
        next(iter(line_stream))
    read_lines = [line.line for line in materialized_line_stream]
    assert read_lines == text_lines
    assert len({line.source_file for line in materialized_line_stream}) > 1

    start_index = 50
    line_stream = line_stream_from_log_directory(
        directory=log_prefix(run.id, JobType.worker),
        cursor_file=f"{log_prefix(run.id, JobType.worker)}12345.log",
        cursor_line_index=start_index,
    )
    materialized_line_stream = list(line_stream)
    assert [line.line for line in materialized_line_stream] == text_lines[start_index:]


@pytest.mark.parametrize(
    "log_preparation_function",
    (
        prepare_logs_v1,
        prepare_logs_v2,
    ),
)
def test_load_inline_logs(
    mock_storage, test_db, log_preparation_function  # noqa: F811
):
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

    result = _load_inline_logs(
        run_id=run.id,
        resolution=resolution,
        still_running=False,
        cursor_file=None,
        cursor_line_index=-1,
        cursor_had_more_before=False,
        max_lines=max_lines,
        filter_strings=[],
    )
    assert not result.more_after  # run isn't alive and resolver logs missing
    assert result.lines == []
    assert result.continuation_cursor is None
    assert result.log_info_message == "Resolver logs are missing"

    log_preparation_function(run.id, text_lines, mock_storage, JobType.driver)

    result = _load_inline_logs(
        run_id=run.id,
        resolution=resolution,
        still_running=False,
        cursor_file=None,
        cursor_line_index=-1,
        cursor_had_more_before=False,
        max_lines=max_lines,
        filter_strings=[],
    )
    assert result.continuation_cursor is not None
    cursor = Cursor.from_token(result.continuation_cursor)
    result.continuation_cursor = None
    assert result == LogLineResult(
        continuation_cursor=None,
        more_before=False,
        more_after=True,
        lines=run_text_lines[:max_lines],
        log_info_message=None,
    )

    result = _load_inline_logs(
        run_id=run.id,
        resolution=resolution,
        still_running=False,
        cursor_file=cursor.source_log_key,
        cursor_line_index=cursor.source_file_line_index,
        cursor_had_more_before=cursor.traversal_had_lines,
        max_lines=max_lines,
        filter_strings=[],
    )
    assert result.continuation_cursor is not None

    cursor = Cursor.from_token(result.continuation_cursor)
    result.continuation_cursor = None

    assert result == LogLineResult(
        continuation_cursor=None,
        more_before=True,
        more_after=True,
        lines=run_text_lines[max_lines:],
        log_info_message=None,
    )

    result = _load_inline_logs(
        run_id=run.id,
        resolution=resolution,
        still_running=False,
        cursor_file=cursor.source_log_key,
        cursor_line_index=cursor.source_file_line_index,
        cursor_had_more_before=cursor.traversal_had_lines,
        max_lines=max_lines,
        filter_strings=[],
    )
    result.continuation_cursor = None
    assert result == LogLineResult(
        continuation_cursor=None,
        more_before=True,
        more_after=False,
        lines=[],
        log_info_message="No matching log lines.",
    )


@pytest.mark.parametrize(
    "log_preparation_function",
    (
        prepare_logs_v1,
        prepare_logs_v2,
    ),
)
def test_load_log_lines(mock_storage, test_db, log_preparation_function):  # noqa: F811
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
        log_info_message="Resolution has not started yet.",
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
        log_info_message="The run has not yet started executing.",
    )

    run.future_state = FutureState.SCHEDULED
    run.external_jobs = (
        ExternalJob(kind="fake", try_number=0, external_job_id="fake"),
    )
    save_run(run)
    text_lines = [line.line for line in finite_logs(100)]
    log_preparation_function(run.id, text_lines, mock_storage, JobType.worker)

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
        log_info_message=None,
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
        log_info_message=None,
    )

    result = load_log_lines(
        run_id=run.id,
        continuation_cursor=token,
        max_lines=max_lines,
    )
    result.continuation_cursor = None
    assert result == LogLineResult(
        continuation_cursor=None,
        more_before=True,
        more_after=True,
        lines=[],
        log_info_message="No matching log lines.",
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


@pytest.mark.parametrize(
    "log_preparation_function",
    (
        prepare_logs_v1,
        prepare_logs_v2,
    ),
)
def test_load_cloned_run_log_lines(
    mock_storage, test_db, log_preparation_function  # noqa: F811
):
    run = make_run(future_state=FutureState.CREATED)
    save_run(run)
    resolution = make_resolution(status=ResolutionStatus.SCHEDULED)
    resolution.root_id = run.root_id
    save_resolution(resolution)
    max_lines = 50

    cloned_run = make_run(future_state=FutureState.CREATED, original_run_id=run.id)
    save_run(cloned_run)
    cloned_resolution = make_resolution(status=ResolutionStatus.SCHEDULED)
    cloned_resolution.root_id = cloned_run.root_id
    save_resolution(cloned_resolution)

    result = load_log_lines(
        run_id=cloned_run.id,
        continuation_cursor=None,
        max_lines=max_lines,
    )
    result.continuation_cursor = None
    assert result == LogLineResult(
        continuation_cursor=None,
        more_before=False,
        more_after=True,
        lines=[],
        log_info_message="Resolution has not started yet.",
    )

    resolution.status = ResolutionStatus.RUNNING
    save_resolution(resolution)

    result = load_log_lines(
        run_id=cloned_run.id,
        continuation_cursor=None,
        max_lines=max_lines,
    )
    result.continuation_cursor = None
    assert result == LogLineResult(
        continuation_cursor=None,
        more_before=False,
        more_after=True,
        lines=[],
        log_info_message="The run has not yet started executing.",
    )

    run.future_state = FutureState.SCHEDULED
    run.external_jobs = (
        ExternalJob(kind="fake", try_number=0, external_job_id="fake"),
    )
    save_run(run)
    text_lines = [line.line for line in finite_logs(100)]
    log_preparation_function(run.id, text_lines, mock_storage, JobType.worker)

    result = load_log_lines(
        run_id=cloned_run.id,
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
        log_info_message=f"Run logs sourced from original run {run.id}.",
    )

    result = load_log_lines(
        run_id=cloned_run.id,
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
        log_info_message=f"Run logs sourced from original run {run.id}.",
    )

    result = load_log_lines(
        run_id=cloned_run.id,
        continuation_cursor=token,
        max_lines=max_lines,
    )
    result.continuation_cursor = None
    assert result == LogLineResult(
        continuation_cursor=None,
        more_before=True,
        more_after=True,
        lines=[],
        log_info_message="No matching log lines.",
    )

    result = load_log_lines(
        run_id=cloned_run.id,
        continuation_cursor=None,
        max_lines=1,
        filter_strings=["2", "4"],
    )
    assert result.lines == ["Line 24"]

    result = load_log_lines(
        run_id=cloned_run.id,
        continuation_cursor=result.continuation_cursor,
        max_lines=1,
        filter_strings=["2", "4"],
    )
    assert result.lines == ["Line 42"]


def test_continue_from_end_with_no_new_logs(test_db, mock_storage):  # noqa: F811
    run = make_run(future_state=FutureState.SCHEDULED)
    save_run(run)

    max_lines = 50
    break_at_line = 52
    total_lines = 100
    text_lines = [line.line for line in finite_logs(total_lines)]

    # Emulate a scenario where:
    # - 50 lines requested, 52 lines produced
    # - return lines 0-50
    # - 50 more lines requested
    # - return lines 50-52
    # - lines 52-100 produced
    # - 50 more lines requested
    # - lines 52-100 returned

    prepare_logs_v2(
        run.id,
        text_lines,
        mock_storage,
        JobType.worker,
        break_at_line=break_at_line,
        emulate_pending_more_lines=True,
    )

    # 50 lines requested, 50 returned
    result = _load_non_inline_logs(
        run_id=run.id,
        still_running=True,
        cursor_file=None,
        cursor_line_index=-1,
        cursor_had_more_before=False,
        max_lines=max_lines,
        filter_strings=[],
    )
    assert result.continuation_cursor is not None
    cursor = Cursor.from_token(result.continuation_cursor)
    assert cursor.traversal_had_lines
    result.continuation_cursor = None
    assert result == LogLineResult(
        continuation_cursor=None,
        more_before=False,
        more_after=True,
        lines=text_lines[:max_lines],
        log_info_message=None,
    )

    # 50 more lines requested, only 2 more available
    result = _load_non_inline_logs(
        run_id=run.id,
        still_running=True,
        cursor_file=cursor.source_log_key,
        cursor_line_index=cursor.source_file_line_index,
        cursor_had_more_before=cursor.traversal_had_lines,
        max_lines=max_lines,
        filter_strings=[],
    )
    assert result.continuation_cursor is not None
    cursor = Cursor.from_token(result.continuation_cursor)
    result.continuation_cursor = None
    assert result == LogLineResult(
        continuation_cursor=None,
        more_before=True,
        more_after=True,
        lines=text_lines[max_lines:break_at_line],  # noqa: E203
        log_info_message=None,
    )

    # 50 more lines requested, no more available
    result = _load_non_inline_logs(
        run_id=run.id,
        still_running=True,
        cursor_file=cursor.source_log_key,
        cursor_line_index=cursor.source_file_line_index,
        cursor_had_more_before=cursor.traversal_had_lines,
        max_lines=max_lines,
        filter_strings=[],
    )
    assert result.continuation_cursor is not None
    cursor = Cursor.from_token(result.continuation_cursor)
    result.continuation_cursor = None
    assert result == LogLineResult(
        continuation_cursor=None,
        more_before=True,
        more_after=True,
        lines=[],  # noqa: E203
        log_info_message="No matching log lines.",
    )

    # upload more logs
    prepare_logs_v2(
        run.id,
        text_lines,
        mock_storage,
        JobType.worker,
        break_at_line=break_at_line,
        emulate_pending_more_lines=False,
    )

    # 50 more lines requested, 48 more available
    result = _load_non_inline_logs(
        run_id=run.id,
        still_running=True,
        cursor_file=cursor.source_log_key,
        cursor_line_index=cursor.source_file_line_index,
        cursor_had_more_before=cursor.traversal_had_lines,
        max_lines=max_lines,
        filter_strings=[],
    )
    assert result.continuation_cursor is not None
    result.continuation_cursor = None
    assert result == LogLineResult(
        continuation_cursor=None,
        more_before=True,
        more_after=True,
        lines=text_lines[break_at_line:total_lines],  # noqa: E203
        log_info_message=None,
    )
