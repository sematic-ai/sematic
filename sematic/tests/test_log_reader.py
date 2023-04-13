# Standard Library
import sys
from typing import Iterable, List

# Third-party
import pytest

# Sematic
from sematic.abstract_future import FutureState
from sematic.api.tests.fixtures import mock_storage  # noqa: F401
from sematic.db.models.resolution import ResolutionStatus
from sematic.db.queries import save_job, save_resolution, save_run
from sematic.db.tests.fixtures import (  # noqa: F401
    allow_any_run_state_transition,
    make_job,
    make_resolution,
    make_run,
    test_db,
)
from sematic.log_reader import (
    Cursor,
    LogLine,
    LogLineResult,
    _load_inline_logs,
    _load_non_inline_logs,
    _stream_from_text_stream_from_index,
    get_log_lines_from_line_stream,
    line_stream_from_log_directory,
    load_log_lines,
    log_prefix,
    reversed,
    to_line_id,
)
from sematic.resolvers.cloud_resolver import (
    END_INLINE_RUN_INDICATOR,
    START_INLINE_RUN_INDICATOR,
)
from sematic.scheduling.job_details import JobKind

_streamed_lines: List[str] = []
_DUMMY_LOGS_FILE = "logs123.log"
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


def yield_from_cursor(
    log_lines: Iterable[LogLine], cursor_file, cursor_index
) -> Iterable[LogLine]:
    for line in log_lines:
        if cursor_file is None or cursor_index is None:
            yield line
        elif (line.source_file, line.source_file_index) >= (cursor_file, cursor_index):
            yield line


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
        cursor_file=None,
        cursor_line_index=-1,
        traversal_had_lines=False,
        max_lines=max_lines,
        filter_strings=[],
        run_id=_DUMMY_RUN_ID,
    )
    cursor = Cursor.from_token(result.forward_cursor_token)
    compare_log_line_result(
        LogLineResult(
            can_continue_forward=True,
            can_continue_backward=True,
            forward_cursor_token=None,
            reverse_cursor_token=None,
            lines=[f"Line {i}" for i in range(max_lines)],
            line_ids=None,
            log_info_message=None,
        ),
        result,
    )
    assert _streamed_lines == result.lines

    # emulate continuation
    result = get_log_lines_from_line_stream(
        line_stream=yield_from_cursor(
            infinite_logs(), cursor.source_log_key, cursor.source_file_line_index
        ),
        still_running=True,
        cursor_file=cursor.source_log_key,
        cursor_line_index=cursor.source_file_line_index,
        traversal_had_lines=cursor.traversal_had_lines,
        max_lines=max_lines,
        filter_strings=[],
        run_id=_DUMMY_RUN_ID,
    )
    compare_log_line_result(
        LogLineResult(
            can_continue_backward=True,
            can_continue_forward=True,
            forward_cursor_token=None,
            reverse_cursor_token=None,
            lines=[f"Line {i}" for i in range(max_lines, 2 * max_lines)],
            line_ids=None,
            log_info_message=None,
        ),
        result,
    )


def test_get_log_lines_from_line_stream_more_after():
    max_lines = 200
    kwargs = dict(
        cursor_file=None,
        cursor_line_index=-1,
        traversal_had_lines=False,
        max_lines=max_lines,
        filter_strings=[],
        run_id=_DUMMY_RUN_ID,
    )
    result = get_log_lines_from_line_stream(
        line_stream=infinite_logs(),
        still_running=True,
        **kwargs,
    )
    assert result.can_continue_forward

    result = get_log_lines_from_line_stream(
        line_stream=finite_logs(max_lines - 1),
        still_running=True,
        **kwargs,
    )
    assert result.can_continue_forward

    result = get_log_lines_from_line_stream(
        line_stream=finite_logs(max_lines - 1),
        still_running=False,
        **kwargs,
    )
    assert not result.can_continue_forward


def test_get_log_lines_from_line_stream_filter():
    max_lines = 10
    result = get_log_lines_from_line_stream(
        line_stream=fake_streamer(infinite_logs()),
        still_running=True,
        cursor_file=None,
        cursor_line_index=-1,
        traversal_had_lines=False,
        run_id=_DUMMY_RUN_ID,
        max_lines=max_lines,
        filter_strings=["2"],
    )
    cursor = Cursor.from_token(result.forward_cursor_token)

    compare_log_line_result(
        LogLineResult(
            can_continue_forward=True,
            can_continue_backward=True,
            forward_cursor_token=None,
            reverse_cursor_token=None,
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
            line_ids=None,
            log_info_message=None,
        ),
        result,
    )

    result = get_log_lines_from_line_stream(
        line_stream=yield_from_cursor(
            infinite_logs(), cursor.source_log_key, cursor.source_file_line_index
        ),
        still_running=True,
        cursor_file=cursor.source_log_key,
        cursor_line_index=cursor.source_file_line_index,
        traversal_had_lines=cursor.traversal_had_lines,
        run_id=_DUMMY_RUN_ID,
        max_lines=max_lines,
        filter_strings=["2"],
    )

    compare_log_line_result(
        LogLineResult(
            can_continue_forward=True,
            can_continue_backward=True,
            forward_cursor_token=None,
            reverse_cursor_token=None,
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
            line_ids=None,
            log_info_message=None,
        ),
        result,
    )


def prepare_logs_v2(
    run_id,
    text_lines,
    mock_storage,  # noqa: F811
    job_kind,
    break_at_line=52,
    emulate_pending_more_lines=False,
):
    lines_part_1 = text_lines[:break_at_line]
    lines_part_2 = text_lines[break_at_line:]

    log_file_contents_part_1 = bytes("\n".join(lines_part_1), encoding="utf8")
    prefix = log_prefix(run_id, job_kind)
    key_part_1 = f"{prefix}1600000000000.log"
    mock_storage.set(key_part_1, log_file_contents_part_1)

    if emulate_pending_more_lines:
        # act as if the second file hasn't been produced yet
        return prefix
    log_file_contents_part_2 = bytes("\n".join(lines_part_2), encoding="utf8")
    prefix = log_prefix(run_id, job_kind)
    key_part_2 = f"{prefix}1610000000000.log"
    mock_storage.set(key_part_2, log_file_contents_part_2)

    line_ids_part_1 = [to_line_id(key_part_1, i) for i in range(len(lines_part_1))]
    line_ids_part_2 = [to_line_id(key_part_2, i) for i in range(len(lines_part_2))]
    line_ids = line_ids_part_1 + line_ids_part_2
    return prefix, line_ids


@pytest.mark.parametrize(
    "log_preparation_function",
    (prepare_logs_v2,),
)
def test_load_non_inline_logs(
    test_db,  # noqa: F811
    mock_storage,  # noqa: F811
    log_preparation_function,
    allow_any_run_state_transition,  # noqa: F811
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
        traversal_had_lines=False,
        max_lines=max_lines,
        filter_strings=[],
        reverse=False,
    )
    assert (
        not result.can_continue_forward
    )  # run isn't running and there are no logfiles
    assert result.lines == []
    assert result.forward_cursor_token is None
    assert result.log_info_message == "No log files found"
    log_preparation_function(run.id, text_lines, mock_storage, JobKind.run)

    result = _load_non_inline_logs(
        run_id=run.id,
        still_running=False,
        cursor_file=None,
        cursor_line_index=-1,
        traversal_had_lines=False,
        max_lines=max_lines,
        filter_strings=[],
        reverse=False,
    )
    assert result.forward_cursor_token is not None
    cursor = Cursor.from_token(result.forward_cursor_token)
    assert cursor.traversal_had_lines
    compare_log_line_result(
        LogLineResult(
            can_continue_forward=True,
            can_continue_backward=True,
            forward_cursor_token=None,
            reverse_cursor_token=None,
            lines=text_lines[:max_lines],
            line_ids=None,
            log_info_message=None,
        ),
        result,
    )

    result = _load_non_inline_logs(
        run_id=run.id,
        still_running=False,
        cursor_file=cursor.source_log_key,
        cursor_line_index=cursor.source_file_line_index,
        traversal_had_lines=cursor.traversal_had_lines,
        max_lines=max_lines,
        filter_strings=[],
        reverse=False,
    )
    assert result.forward_cursor_token is not None
    cursor = Cursor.from_token(result.forward_cursor_token)
    compare_log_line_result(
        LogLineResult(
            forward_cursor_token=None,
            reverse_cursor_token=None,
            can_continue_backward=True,
            can_continue_forward=True,
            lines=text_lines[max_lines : 2 * max_lines],  # noqa: E203
            line_ids=None,
            log_info_message=None,
        ),
        result,
    )

    result = _load_non_inline_logs(
        run_id=run.id,
        still_running=False,
        cursor_file=cursor.source_log_key,
        cursor_line_index=cursor.source_file_line_index,
        traversal_had_lines=cursor.traversal_had_lines,
        max_lines=max_lines,
        filter_strings=[],
        reverse=False,
    )
    result.reverse_cursor_token = None
    assert result == LogLineResult(
        can_continue_forward=False,
        can_continue_backward=True,
        forward_cursor_token=None,
        reverse_cursor_token=None,
        lines=[],
        line_ids=[],
        log_info_message="No matching log lines.",
    )


def test_line_stream_from_log_directory(
    mock_storage, test_db, allow_any_run_state_transition  # noqa: F811
):
    run = make_run(future_state=FutureState.RESOLVED)
    save_run(run)
    line_stream = line_stream_from_log_directory("empty", None, None, reverse=False)
    materialized_line_stream = list(line_stream)
    assert materialized_line_stream == []

    n_lines = 500
    text_lines = [f"Line {i}" for i in range(n_lines)]
    prefix, _ = prepare_logs_v2(
        run_id=run.id,
        text_lines=text_lines,
        mock_storage=mock_storage,
        job_kind=JobKind.run,
    )
    line_stream = line_stream_from_log_directory(prefix, None, None, reverse=False)
    materialized_line_stream = list(line_stream)
    with pytest.raises(StopIteration):
        # if it was a generator as expected, we exhausted it when we materialized it
        next(iter(line_stream))
    read_lines = [line.line for line in materialized_line_stream]
    assert read_lines == text_lines
    assert len({line.source_file for line in materialized_line_stream}) > 1

    start_index = 50
    line_stream = line_stream_from_log_directory(
        directory=log_prefix(run.id, JobKind.run),
        cursor_file=f"{log_prefix(run.id, JobKind.run)}1600000000000.log",
        cursor_line_index=start_index,
        reverse=False,
    )
    materialized_line_stream = list(line_stream)
    assert [line.line for line in materialized_line_stream] == text_lines[start_index:]


def test_line_stream_from_log_directory_reverse(
    mock_storage, test_db, allow_any_run_state_transition  # noqa: F811
):
    run = make_run(future_state=FutureState.RESOLVED)
    break_at_line = 52
    save_run(run)
    n_lines = 500
    text_lines = [f"Line {i}" for i in range(n_lines)]
    prefix, _ = prepare_logs_v2(
        run_id=run.id,
        text_lines=text_lines,
        mock_storage=mock_storage,
        job_kind=JobKind.run,
        break_at_line=break_at_line,
    )
    line_stream = line_stream_from_log_directory(prefix, None, None, reverse=True)
    materialized_line_stream = list(line_stream)
    with pytest.raises(StopIteration):
        # if it was a generator as expected, we exhausted it when we materialized it
        next(iter(line_stream))
    read_lines = [line.line for line in materialized_line_stream]
    assert read_lines == list(reversed(text_lines))
    assert len({line.source_file for line in materialized_line_stream}) > 1

    start_index = 20
    line_stream = line_stream_from_log_directory(
        directory=log_prefix(run.id, JobKind.run),
        cursor_file=f"{log_prefix(run.id, JobKind.run)}1610000000000.log",
        cursor_line_index=start_index,
        reverse=True,
    )
    materialized_line_stream = list(line_stream)
    assert [line.line for line in materialized_line_stream] == list(
        reversed(text_lines[: start_index + break_at_line])
    )


@pytest.mark.parametrize(
    "log_preparation_function",
    (prepare_logs_v2,),
)
def test_load_inline_logs(
    mock_storage,  # noqa: F811
    test_db,  # noqa: F811
    log_preparation_function,
    allow_any_run_state_transition,  # noqa: F811
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
        traversal_had_lines=False,
        max_lines=max_lines,
        filter_strings=[],
    )
    assert not result.can_continue_forward  # run isn't alive and resolver logs missing
    assert result.lines == []
    assert result.forward_cursor_token is None
    assert result.log_info_message == "Resolver logs are missing"

    log_preparation_function(run.id, text_lines, mock_storage, JobKind.resolver)

    result = _load_inline_logs(
        run_id=run.id,
        resolution=resolution,
        still_running=False,
        cursor_file=None,
        cursor_line_index=-1,
        traversal_had_lines=False,
        max_lines=max_lines,
        filter_strings=[],
    )
    assert result.forward_cursor_token is not None
    cursor = Cursor.from_token(result.forward_cursor_token)
    result.forward_cursor_token = None
    result.reverse_cursor_token = None
    compare_log_line_result(
        LogLineResult(
            can_continue_forward=True,
            can_continue_backward=True,
            forward_cursor_token=None,
            reverse_cursor_token=None,
            lines=run_text_lines[:max_lines],
            line_ids=None,
            log_info_message=None,
        ),
        result,
    )

    result = _load_inline_logs(
        run_id=run.id,
        resolution=resolution,
        still_running=False,
        cursor_file=cursor.source_log_key,
        cursor_line_index=cursor.source_file_line_index,
        traversal_had_lines=cursor.traversal_had_lines,
        max_lines=max_lines,
        filter_strings=[],
    )
    assert result.forward_cursor_token is not None

    cursor = Cursor.from_token(result.forward_cursor_token)
    result.forward_cursor_token = None
    result.reverse_cursor_token = None

    compare_log_line_result(
        LogLineResult(
            forward_cursor_token=None,
            can_continue_backward=True,
            can_continue_forward=True,
            lines=run_text_lines[max_lines:],
            line_ids=None,
            log_info_message=None,
        ),
        result,
    )

    result = _load_inline_logs(
        run_id=run.id,
        resolution=resolution,
        still_running=False,
        cursor_file=cursor.source_log_key,
        cursor_line_index=cursor.source_file_line_index,
        traversal_had_lines=cursor.traversal_had_lines,
        max_lines=max_lines,
        filter_strings=[],
    )
    compare_log_line_result(
        LogLineResult(
            can_continue_forward=False,
            can_continue_backward=True,
            forward_cursor_token=None,
            reverse_cursor_token=None,
            lines=[],
            line_ids=None,
            log_info_message="No matching log lines.",
        ),
        result,
    )


@pytest.mark.parametrize(
    "log_preparation_function",
    (prepare_logs_v2,),
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
        forward_cursor_token=None,
        reverse_cursor_token=None,
        max_lines=max_lines,
        reverse=False,
    )
    result.forward_cursor_token = None
    result.reverse_cursor_token = None
    assert result == LogLineResult(
        can_continue_forward=True,
        can_continue_backward=False,
        forward_cursor_token=None,
        reverse_cursor_token=None,
        lines=[],
        line_ids=[],
        log_info_message="Resolution has not started yet.",
    )

    resolution.status = ResolutionStatus.RUNNING
    save_resolution(resolution)

    result = load_log_lines(
        run_id=run.id,
        forward_cursor_token=None,
        reverse_cursor_token=None,
        max_lines=max_lines,
        reverse=False,
    )
    result.forward_cursor_token = None
    assert result == LogLineResult(
        can_continue_forward=True,
        can_continue_backward=False,
        forward_cursor_token=None,
        reverse_cursor_token=None,
        lines=[],
        line_ids=[],
        log_info_message="The run has not yet started executing.",
    )

    run.future_state = FutureState.SCHEDULED
    save_job(make_job(run_id=run.id))
    save_run(run)
    text_lines = [line.line for line in finite_logs(100)]
    _, line_ids = log_preparation_function(
        run.id, text_lines, mock_storage, JobKind.run
    )

    result = load_log_lines(
        run_id=run.id,
        forward_cursor_token=None,
        reverse_cursor_token=None,
        max_lines=max_lines,
    )
    token = result.forward_cursor_token
    compare_log_line_result(
        LogLineResult(
            forward_cursor_token=None,
            reverse_cursor_token=None,
            can_continue_backward=True,
            can_continue_forward=True,
            lines=text_lines[:max_lines],
            line_ids=line_ids[:max_lines],
            log_info_message=None,
        ),
        result,
        compare_line_ids=True,
    )

    result = load_log_lines(
        run_id=run.id,
        forward_cursor_token=token,
        reverse_cursor_token=None,
        max_lines=max_lines,
        reverse=False,
    )
    token = result.forward_cursor_token
    compare_log_line_result(
        LogLineResult(
            can_continue_forward=True,
            can_continue_backward=True,
            forward_cursor_token=None,
            reverse_cursor_token=None,
            lines=text_lines[max_lines : 2 * max_lines],  # noqa: E203
            line_ids=None,
            log_info_message=None,
        ),
        result,
    )

    result = load_log_lines(
        run_id=run.id,
        forward_cursor_token=token,
        reverse_cursor_token=None,
        max_lines=max_lines,
        reverse=False,
    )
    compare_log_line_result(
        LogLineResult(
            can_continue_forward=True,
            can_continue_backward=True,
            forward_cursor_token=None,
            reverse_cursor_token=None,
            lines=[],
            line_ids=[],
            log_info_message="No matching log lines.",
        ),
        result,
        compare_line_ids=True,
    )

    result = load_log_lines(
        run_id=run.id,
        forward_cursor_token=None,
        reverse_cursor_token=None,
        max_lines=1,
        filter_strings=["2", "4"],
        reverse=False,
    )
    assert result.lines == ["Line 24"]

    result = load_log_lines(
        run_id=run.id,
        forward_cursor_token=result.forward_cursor_token,
        reverse_cursor_token=None,
        max_lines=1,
        filter_strings=["2", "4"],
        reverse=False,
    )
    assert result.lines == ["Line 42"]


@pytest.mark.parametrize(
    "log_preparation_function",
    (prepare_logs_v2,),
)
def test_load_log_lines_reverse(
    mock_storage, test_db, log_preparation_function  # noqa: F811
):  # noqa: F811
    run = make_run(future_state=FutureState.CREATED)
    save_run(run)
    resolution = make_resolution(status=ResolutionStatus.SCHEDULED)
    resolution.root_id = run.root_id
    save_resolution(resolution)
    max_lines = 50

    result = load_log_lines(
        run_id=run.id,
        forward_cursor_token=None,
        reverse_cursor_token=None,
        max_lines=max_lines,
        reverse=True,
    )
    assert result.forward_cursor_token is not None
    result.forward_cursor_token = None
    assert result == LogLineResult(
        can_continue_forward=True,
        can_continue_backward=False,
        forward_cursor_token=None,
        reverse_cursor_token=None,
        lines=[],
        line_ids=[],
        log_info_message="Resolution has not started yet.",
    )

    resolution.status = ResolutionStatus.RUNNING
    save_resolution(resolution)

    result = load_log_lines(
        run_id=run.id,
        forward_cursor_token=None,
        reverse_cursor_token=None,
        max_lines=max_lines,
        reverse=True,
    )
    assert result.forward_cursor_token is not None
    result.forward_cursor_token = None
    assert result == LogLineResult(
        can_continue_forward=True,
        can_continue_backward=False,
        forward_cursor_token=None,
        reverse_cursor_token=None,
        lines=[],
        line_ids=[],
        log_info_message="The run has not yet started executing.",
    )

    run.future_state = FutureState.SCHEDULED
    save_job(make_job(run_id=run.id))
    save_run(run)
    text_lines = [line.line for line in finite_logs(100)]
    _, line_ids = log_preparation_function(
        run.id, text_lines, mock_storage, JobKind.run
    )

    result = load_log_lines(
        run_id=run.id,
        forward_cursor_token=None,
        reverse_cursor_token=None,
        max_lines=max_lines,
        reverse=True,
    )
    token = result.reverse_cursor_token
    compare_log_line_result(
        LogLineResult(
            forward_cursor_token=None,
            reverse_cursor_token=None,
            can_continue_backward=True,
            can_continue_forward=True,
            lines=text_lines[-1 * max_lines :],  # noqa: E203
            line_ids=line_ids[-1 * max_lines :],  # noqa: E203
            log_info_message=None,
        ),
        result,
        compare_line_ids=True,
    )

    result = load_log_lines(
        run_id=run.id,
        forward_cursor_token=None,
        reverse_cursor_token=token,
        max_lines=max_lines,
        reverse=True,
    )
    token = result.reverse_cursor_token
    compare_log_line_result(
        LogLineResult(
            can_continue_forward=True,
            can_continue_backward=True,
            forward_cursor_token=None,
            reverse_cursor_token=None,
            lines=text_lines[-2 * max_lines : -1 * max_lines],  # noqa: E203
            line_ids=None,
            log_info_message=None,
        ),
        result,
    )

    result = load_log_lines(
        run_id=run.id,
        forward_cursor_token=None,
        reverse_cursor_token=token,
        max_lines=max_lines,
        reverse=True,
    )
    compare_log_line_result(
        LogLineResult(
            can_continue_forward=True,
            can_continue_backward=False,
            forward_cursor_token=None,
            reverse_cursor_token=None,
            lines=[],
            line_ids=None,
            log_info_message="No matching log lines.",
        ),
        result,
    )
    result = load_log_lines(
        run_id=run.id,
        forward_cursor_token=None,
        reverse_cursor_token=None,
        max_lines=1,
        filter_strings=["2", "4"],
        reverse=True,
    )
    assert result.lines == ["Line 42"]

    result = load_log_lines(
        run_id=run.id,
        forward_cursor_token=None,
        reverse_cursor_token=result.reverse_cursor_token,
        max_lines=1,
        filter_strings=["2", "4"],
        reverse=True,
    )
    assert result.lines == ["Line 24"]


@pytest.mark.parametrize(
    "log_preparation_function",
    (prepare_logs_v2,),
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
        forward_cursor_token=None,
        reverse_cursor_token=None,
        max_lines=max_lines,
        reverse=False,
    )
    result.forward_cursor_token = None
    result.reverse_cursor_token = None
    assert result == LogLineResult(
        forward_cursor_token=None,
        reverse_cursor_token=None,
        can_continue_backward=False,
        can_continue_forward=True,
        lines=[],
        line_ids=[],
        log_info_message="Resolution has not started yet.",
    )

    resolution.status = ResolutionStatus.RUNNING
    save_resolution(resolution)

    result = load_log_lines(
        run_id=cloned_run.id,
        forward_cursor_token=None,
        reverse_cursor_token=None,
        max_lines=max_lines,
        reverse=False,
    )
    compare_log_line_result(
        LogLineResult(
            can_continue_forward=True,
            can_continue_backward=False,
            forward_cursor_token=None,
            reverse_cursor_token=None,
            lines=[],
            line_ids=[],
            log_info_message="The run has not yet started executing.",
        ),
        result,
    )

    run.future_state = FutureState.SCHEDULED
    save_job(make_job(run_id=run.id))
    save_run(run)
    text_lines = [line.line for line in finite_logs(100)]
    log_preparation_function(run.id, text_lines, mock_storage, JobKind.run)

    result = load_log_lines(
        run_id=cloned_run.id,
        forward_cursor_token=None,
        reverse_cursor_token=None,
        max_lines=max_lines,
        reverse=False,
    )
    token = result.forward_cursor_token
    compare_log_line_result(
        LogLineResult(
            can_continue_forward=True,
            can_continue_backward=True,
            forward_cursor_token=None,
            reverse_cursor_token=None,
            lines=text_lines[:max_lines],
            line_ids=None,
            log_info_message=f"Run logs sourced from original run {run.id}.",
        ),
        result,
    )

    result = load_log_lines(
        run_id=cloned_run.id,
        forward_cursor_token=token,
        reverse_cursor_token=None,
        max_lines=max_lines,
        reverse=False,
    )
    token = result.forward_cursor_token
    compare_log_line_result(
        LogLineResult(
            can_continue_forward=True,
            can_continue_backward=True,
            forward_cursor_token=None,
            reverse_cursor_token=None,
            lines=text_lines[max_lines : 2 * max_lines],  # noqa: E203
            line_ids=None,
            log_info_message=f"Run logs sourced from original run {run.id}.",
        ),
        result,
    )

    result = load_log_lines(
        run_id=cloned_run.id,
        forward_cursor_token=token,
        reverse_cursor_token=None,
        max_lines=max_lines,
        reverse=False,
    )
    result.forward_cursor_token = None
    result.reverse_cursor_token = None
    assert result == LogLineResult(
        forward_cursor_token=None,
        reverse_cursor_token=None,
        can_continue_backward=True,
        can_continue_forward=True,
        lines=[],
        line_ids=[],
        log_info_message="No matching log lines.",
    )

    result = load_log_lines(
        run_id=cloned_run.id,
        forward_cursor_token=None,
        reverse_cursor_token=None,
        max_lines=1,
        filter_strings=["2", "4"],
        reverse=False,
    )
    assert result.lines == ["Line 24"]

    result = load_log_lines(
        run_id=cloned_run.id,
        forward_cursor_token=result.forward_cursor_token,
        reverse_cursor_token=None,
        max_lines=1,
        filter_strings=["2", "4"],
        reverse=False,
    )
    assert result.lines == ["Line 42"]


def test_continue_from_end_with_no_new_logs(
    test_db, mock_storage, allow_any_run_state_transition  # noqa: F811
):
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
        JobKind.run,
        break_at_line=break_at_line,
        emulate_pending_more_lines=True,
    )

    # 50 lines requested, 50 returned
    result = _load_non_inline_logs(
        run_id=run.id,
        still_running=True,
        cursor_file=None,
        cursor_line_index=-1,
        traversal_had_lines=False,
        max_lines=max_lines,
        filter_strings=[],
        reverse=False,
    )
    assert result.forward_cursor_token is not None
    assert result.reverse_cursor_token is not None
    cursor = Cursor.from_token(result.forward_cursor_token)
    assert cursor.traversal_had_lines
    compare_log_line_result(
        LogLineResult(
            can_continue_forward=True,
            can_continue_backward=True,
            forward_cursor_token=None,
            reverse_cursor_token=None,
            lines=text_lines[:max_lines],
            line_ids=None,
            log_info_message=None,
        ),
        result,
    )

    # 50 more lines requested, only 2 more available
    result = _load_non_inline_logs(
        run_id=run.id,
        still_running=True,
        cursor_file=cursor.source_log_key,
        cursor_line_index=cursor.source_file_line_index,
        traversal_had_lines=cursor.traversal_had_lines,
        max_lines=max_lines,
        filter_strings=[],
        reverse=False,
    )
    assert result.forward_cursor_token is not None
    assert result.reverse_cursor_token is not None
    cursor = Cursor.from_token(result.forward_cursor_token)
    compare_log_line_result(
        LogLineResult(
            can_continue_forward=True,
            can_continue_backward=True,
            forward_cursor_token=None,
            reverse_cursor_token=None,
            lines=text_lines[max_lines:break_at_line],  # noqa: E203
            line_ids=None,
            log_info_message=None,
        ),
        result,
    )

    # 50 more lines requested, no more available
    result = _load_non_inline_logs(
        run_id=run.id,
        still_running=True,
        cursor_file=cursor.source_log_key,
        cursor_line_index=cursor.source_file_line_index,
        traversal_had_lines=cursor.traversal_had_lines,
        max_lines=max_lines,
        filter_strings=[],
        reverse=False,
    )
    assert result.forward_cursor_token is not None
    assert result.reverse_cursor_token is not None
    cursor = Cursor.from_token(result.forward_cursor_token)
    compare_log_line_result(
        LogLineResult(
            can_continue_forward=True,
            can_continue_backward=True,
            forward_cursor_token=None,
            reverse_cursor_token=None,
            lines=[],  # noqa: E203
            line_ids=[],
            log_info_message="No matching log lines.",
        ),
        result,
    )

    # upload more logs
    prepare_logs_v2(
        run.id,
        text_lines,
        mock_storage,
        JobKind.run,
        break_at_line=break_at_line,
        emulate_pending_more_lines=False,
    )

    # 50 more lines requested, 48 more available
    result = _load_non_inline_logs(
        run_id=run.id,
        still_running=True,
        cursor_file=cursor.source_log_key,
        cursor_line_index=cursor.source_file_line_index,
        traversal_had_lines=cursor.traversal_had_lines,
        max_lines=max_lines,
        filter_strings=[],
        reverse=False,
    )
    assert result.forward_cursor_token is not None
    assert result.reverse_cursor_token is not None
    compare_log_line_result(
        LogLineResult(
            can_continue_forward=True,
            can_continue_backward=True,
            forward_cursor_token=None,
            reverse_cursor_token=None,
            lines=text_lines[break_at_line:total_lines],  # noqa: E203
            line_ids=None,
            log_info_message=None,
        ),
        result,
    )


def test_stream_from_text_stream_from_index_forward():
    log_file = "logs123.log"
    n_lines = 100
    text_stream = (f"Line {i}" for i in range(n_lines))

    streamed = list(
        _stream_from_text_stream_from_index(
            log_file=log_file,
            start_line_index=0,
            reverse=False,
            text_stream=text_stream,
        )
    )
    assert streamed == list(finite_logs(n_lines))

    start_line_index = 50
    text_stream = (f"Line {i}" for i in range(n_lines))
    streamed = list(
        _stream_from_text_stream_from_index(
            log_file=log_file,
            start_line_index=start_line_index,
            reverse=False,
            text_stream=text_stream,
        )
    )
    assert streamed == list(finite_logs(n_lines))[start_line_index:]


def test_stream_from_text_stream_from_index_reverse():
    log_file = "logs123.log"
    n_lines = 100
    text_stream = (f"Line {i}" for i in range(n_lines))

    streamed = list(
        _stream_from_text_stream_from_index(
            log_file=log_file,
            start_line_index=sys.maxsize,
            reverse=True,
            text_stream=text_stream,
        )
    )
    assert streamed == list(reversed(finite_logs(n_lines)))

    start_line_index = 50
    text_stream = (f"Line {i}" for i in range(n_lines))
    streamed = list(
        _stream_from_text_stream_from_index(
            log_file=log_file,
            start_line_index=start_line_index,
            reverse=True,
            text_stream=text_stream,
        )
    )
    assert streamed == list(reversed(list(finite_logs(n_lines))[:start_line_index]))


# Note: this serves both as a source of individual test cases
# for test_to_line_id, and a list of test cases for
# test_to_line_id_obeys_order
LINE_ID_TESTS = [
    ("foo/1234bar/baz1610000000000.log", 42, 1100000000000042),
    ("foo/1234bar/baz1610000000000.log", 43, 1100000000000043),
    ("foo/1234bar/baz1610000000333.log", 999, 1100000003330999),
    ("foo/1234bar/baz2510000000333.log", 999, 10100000003330999),
]


@pytest.mark.parametrize("log_file, log_index, expected_id", LINE_ID_TESTS)
def test_to_line_id(log_file, log_index, expected_id):
    actual = to_line_id(log_file, log_index)
    assert expected_id == actual


def test_to_line_id_obeys_order():
    """Tests that lines which were generated later have higher ids.

    Even if the actual logic mapping log files/indices to ids changes, this
    test should still pass unchanged.
    """

    # Lexical ordering should ensure these are sorted first by log
    # file, then by line index.
    ordered_lines = sorted(LINE_ID_TESTS)

    line_ids = [to_line_id(log_file, index) for log_file, index, _ in ordered_lines]
    assert sorted(line_ids) == line_ids


def compare_log_line_result(
    expected: LogLineResult,
    actual: LogLineResult,
    compare_cursors: bool = False,
    compare_line_ids: bool = False,
):
    if not compare_cursors:
        expected.forward_cursor_token = None
        expected.reverse_cursor_token = None
        actual.forward_cursor_token = None
        actual.reverse_cursor_token = None
    assert len(actual.line_ids) == len(actual.lines)
    assert sorted(actual.line_ids) == actual.line_ids

    if not compare_line_ids:
        expected.line_ids = None  # type: ignore
        actual.line_ids = None  # type: ignore

    assert expected == actual
