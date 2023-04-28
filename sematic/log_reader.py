# Standard Library
import base64
import json
import logging
import sys
from dataclasses import asdict, dataclass, replace
from enum import Enum, unique
from typing import Iterable, List, Optional, TypeVar

# Sematic
from sematic import api_client
from sematic.abstract_future import FutureState
from sematic.db import queries as db_queries
from sematic.db.models.resolution import Resolution, ResolutionKind, ResolutionStatus
from sematic.db.models.run import Run
from sematic.plugins.abstract_storage import get_storage_plugins
from sematic.plugins.storage.local_storage import LocalStorage
from sematic.resolvers.cloud_resolver import (
    END_INLINE_RUN_INDICATOR,
    START_INLINE_RUN_INDICATOR,
)
from sematic.resolvers.log_streamer import MAX_LINES_PER_LOG_FILE
from sematic.scheduling.job_details import JobKind, JobKindString

V2_LOG_PREFIX = "logs/v2"
LOG_PATH_FORMAT = "{prefix}/run_id/{run_id}/{log_kind}/"

DEFAULT_END_INDEX = sys.maxsize
DEFAULT_START_INDEX = -1

logger = logging.getLogger(__name__)


@unique
class ObjectSource(Enum):
    """When getting objects like runs or resolutions, how should they be fetched?

    Attributes
    ----------
    API:
        Use the API client to query them. Will use your configured API key.
    DB:
        Directly query the DB. Can only be used if you have direct access to the DB.
    """

    API = (api_client,)
    DB = (db_queries,)

    def get_resolution(self, resolution_id: str) -> Resolution:
        return self.value[0].get_resolution(resolution_id)

    def get_run(self, run_id: str) -> Run:
        return self.value[0].get_run(run_id)

    def run_is_inline(self, run_id: str) -> bool:
        """Determine if a scheduled run is inline.

        Looking for jobs to determine inline is only valid
        since we know the run has at least reached SCHEDULED due to it
        not being CREATED.
        """
        if self is ObjectSource.DB:
            has_non_legacy_jobs = self.value[0].count_jobs_by_run_id(run_id) > 0
            if has_non_legacy_jobs:
                return False
            else:
                # TODO: remove this
                # https://github.com/sematic-ai/sematic/issues/710
                return not db_queries.run_has_legacy_jobs(run_id)
        else:
            # we don't look for legacy jobs here, so using the CLI
            # to read logs won't work for old runs. Seems a fair
            # trade off to avoid exposing run_has_legacy_jobs as an
            # API endpoint.
            return len(self.value[0].get_jobs_by_run_id(run_id)) == 0


def log_prefix(run_id: str, job_kind: JobKindString):
    # TODO: move log writing to use "run"/"resolver" instead
    # of "worker"/"driver". Wait to do it until we can add in
    # some backwards compatibility so we can still read logs
    # written by clients that haven't yet upgraded. Probably
    # wait until after deprecating V1, so we don't have to support
    # *3* formats in this module at one time.
    log_kind = "worker" if job_kind == JobKind.run else "driver"
    return LOG_PATH_FORMAT.format(
        prefix=V2_LOG_PREFIX, run_id=run_id, log_kind=log_kind
    )


@dataclass
class LogLineResult:
    """Results of a query for log lines

    Attributes
    ----------
    can_continue_forward:
        Are there more lines after the last line returned? Will be True
        if the answer is known to be yes, False if the answer is known to
        be no. If the answer is not known (i.e. run may still be in
        progress, or we may not know if future lines pass the filter),
        True will be returned. "After" refers to log lines produced
        at a later point in time, regardless of traversal direction. So
        can_continue_forward==True indicates that traversal can continue
        in the forward direction.
    can_continue_backward:
        Are there more lines before the first line returned? Will be True if the
        answer is known to be yes, False if the answer is known to be no. If the
        answer is not known (ex: going in reverse and don't know if earlier lines
        pass the filter), True will be returned. "Before" refers to log lines
        produced at an earlier point in time, regardless of traversal direction. So
        can_continue_backward==True indicates that traversal can continue in the reverse
        direction.
    lines:
        The actual log lines.
    line_ids:
        Unique ids for each included log line. The log line at index `i` of the `lines`
        field will have its id at index `i` of line_ids.
    forward_cursor_token:
        A string that can be used to continue traversing these logs from where you left
        off. If can_continue_forward is False, this will be set to None.
    reverse_cursor_token:
        A string that can be used to continue traversing these logs from where you left
        off, but in the backwards direction. If can_continue_backward is False, this
        will be set to None.
    log_info_message:
        A human-readable extra info message.
    """

    can_continue_forward: bool
    can_continue_backward: bool
    lines: List[str]
    line_ids: List[int]
    forward_cursor_token: Optional[str]
    reverse_cursor_token: Optional[str] = None
    log_info_message: Optional[str] = None


@dataclass
class Cursor:
    """A cursor representing a particular place in the process of traversing logs.

    Attributes
    ----------
    source_log_key:
        The storage key for the log that was being used when the search left off. If no
        logs have been found yet, will be None
    source_file_line_index:
        The line number BEFORE filters are applied within the log file being read.
        It will be the first line that HASN'T yet been read. If no logs have been found
        and `reverse` is False, will be -1. If no logs have been found and `reverse` is
        True, will be `sys.maxsize`.
    filter_strings:
        The filter strings that were used for this log traversal.
    run_id:
        The run id that was being used for this log traversal.
    traversal_had_lines:
        Will be True if this cursor corresponds to a result that has lines, or
        if it continues from a chain of cursors that had found some lines
    reverse:
        Will be True if the lines are being traversed in the reverse direction.
    """

    source_log_key: Optional[str]
    source_file_line_index: int
    filter_strings: List[str]
    run_id: str
    traversal_had_lines: bool = False
    reverse: bool = False

    def to_token(self) -> str:
        return str(
            base64.b64encode(json.dumps(asdict(self)).encode("utf8")), encoding="utf8"
        )

    @classmethod
    def from_token(cls, token: str):
        kwargs = json.loads(
            base64.b64decode(bytes(token, encoding="utf8")).decode("utf8")
        )
        return Cursor(**kwargs)

    @classmethod
    def nothing_found(cls, filter_strings: List[str], run_id: str, reverse: bool):
        return Cursor(
            source_log_key=None,
            source_file_line_index=DEFAULT_END_INDEX
            if reverse
            else DEFAULT_START_INDEX,
            filter_strings=filter_strings,
            run_id=run_id,
            traversal_had_lines=False,
            reverse=reverse,
        )


@dataclass
class LogLine:
    source_file: str
    source_file_index: int
    line: str


def _assert_valid_cursor(cursor: Cursor, run_id: str, filter_strings: Iterable[str]):
    if cursor.run_id != run_id:
        raise ValueError(
            f"Tried to continue a log search of {run_id} using a "
            f"forward cursor from {cursor.run_id}"
        )
    if set(cursor.filter_strings) != set(filter_strings):
        raise ValueError(
            f"Tried to continue a log search of {run_id} using a "
            f"different set of filters than were used in the cursor."
        )


def load_log_lines(
    run_id: str,
    forward_cursor_token: Optional[str],
    reverse_cursor_token: Optional[str],
    max_lines: int,
    filter_strings: Optional[List[str]] = None,
    object_source: ObjectSource = ObjectSource.DB,
    reverse: bool = False,
) -> LogLineResult:
    """Load a portion of the logs for a particular run.

    Parameters
    ----------
    run_id:
        The id of the run to get logs for
    forward_cursor_token:
        A cursor indicating where to continue reading logs from. Should be
        None if the logs are being read from the beginning or `reverse` is
        True. Ignored if `reverse` is True.
    reverse_cursor_token:
        A cursor indicating where to continue reading logs from in the backward
        direction. Should be None if the logs are being read from the end or
        `reverse` is False. Ignored if `reverse` is False.
    max_lines:
        The highest number of log lines that should be returned at once
    filter_strings:
        Only log lines that contain ALL the strings in this list will
        be included in the result
    object_source:
        How to get runs/resolutions
    reverse:
        Whether to traverse logs from the end backwards

    Returns
    -------
    A subset of the logs for the given run
    """
    logger.info(
        "Starting log line loading for: run_id=%s, forward_cursor_token=%s, "
        "reverse_cursor_token=%s, max_lines=%s, filter_strings=%s, reverse=%s",
        run_id,
        forward_cursor_token,
        reverse_cursor_token,
        max_lines,
        filter_strings,
        reverse,
    )
    default_log_info_message = None
    run = object_source.get_run(run_id)

    if run.original_run_id is not None:
        # we source the logs from the original run, and also inform the user of this
        run_id = run.original_run_id
        run = object_source.get_run(run_id)
        default_log_info_message = f"Run logs sourced from original run {run_id}."

    run_state = FutureState[run.future_state]  # type: ignore
    still_running = not (run_state.is_terminal() or run_state == FutureState.RAN)
    resolution = object_source.get_resolution(run.root_id)
    filter_strings = filter_strings if filter_strings is not None else []
    forward_cursor = (
        Cursor.from_token(forward_cursor_token)
        if forward_cursor_token is not None
        else Cursor.nothing_found(filter_strings, run_id, reverse=False)
    )
    reverse_cursor: Cursor = (
        Cursor.from_token(reverse_cursor_token)
        if reverse_cursor_token is not None
        else Cursor.nothing_found(filter_strings, run_id, reverse=True)
    )

    _assert_valid_cursor(forward_cursor, run_id, filter_strings)
    _assert_valid_cursor(reverse_cursor, run_id, filter_strings)

    if ResolutionStatus[resolution.status] in (  # type: ignore
        ResolutionStatus.CREATED,
        ResolutionStatus.SCHEDULED,
    ):
        return LogLineResult(
            can_continue_forward=True,
            can_continue_backward=False,
            lines=[],
            line_ids=[],
            forward_cursor_token=forward_cursor.to_token(),
            reverse_cursor_token=None,
            log_info_message="Resolution has not started yet.",
        )

    filter_strings = filter_strings if filter_strings is not None else []
    if FutureState[run.future_state] == FutureState.CREATED:  # type: ignore
        return LogLineResult(
            can_continue_forward=True,
            can_continue_backward=False,
            lines=[],
            line_ids=[],
            forward_cursor_token=forward_cursor.to_token(),
            reverse_cursor_token=None,
            log_info_message="The run has not yet started executing.",
        )

    cursor_kwargs = (
        dict(
            cursor_file=reverse_cursor.source_log_key,
            cursor_line_index=reverse_cursor.source_file_line_index,
            traversal_had_lines=reverse_cursor.traversal_had_lines,
        )
        if reverse
        else dict(
            cursor_file=forward_cursor.source_log_key,
            cursor_line_index=forward_cursor.source_file_line_index,
            traversal_had_lines=forward_cursor.traversal_had_lines,
        )
    )

    is_inline = object_source.run_is_inline(run.id)
    log_line_result: LogLineResult
    if is_inline:
        log_line_result = _load_inline_logs(
            run_id=run_id,
            resolution=resolution,
            still_running=still_running,
            max_lines=max_lines,
            filter_strings=filter_strings,
            default_log_info_message=default_log_info_message,
            reverse=reverse,
            **cursor_kwargs,  # type: ignore
        )
    else:
        log_line_result = _load_non_inline_logs(
            run_id=run_id,
            still_running=still_running,
            max_lines=max_lines,
            filter_strings=filter_strings,
            default_log_info_message=default_log_info_message,
            reverse=reverse,
            **cursor_kwargs,  # type: ignore
        )

    # when no cursor is set, it means that we are doing the initial pull
    # and we can determine if we can continue in either direction
    # this overrides the value from the `log_line_result`.
    if reverse_cursor_token is None and forward_cursor_token is None:
        if reverse is True:
            # can_continue_forward will be False
            # if the run has reached to a terminal state
            log_line_result = replace(
                log_line_result,
                can_continue_forward=run.future_state
                not in FutureState.terminal_state_strings(),
            )
        else:
            log_line_result = replace(log_line_result, can_continue_backward=False)

    return log_line_result


def _get_latest_log_file(prefix, cursor_file) -> Optional[str]:
    storage = get_storage_plugins([LocalStorage])[0]

    log_files = storage().get_child_paths(prefix)
    if len(log_files) < 1:
        return None

    if cursor_file is not None and cursor_file not in log_files:
        raise RuntimeError(
            f"Trying to continue a log traversal from {cursor_file}, but "
            f"that file doesn't exist."
        )
    latest_log_file = max(
        log_files,
        key=lambda path_key: int(
            path_key.replace(prefix, "").replace(".log", "".replace("/", ""))
        ),
    )
    return latest_log_file


def _load_non_inline_logs(
    run_id: str,
    still_running: bool,
    cursor_file: Optional[str],
    cursor_line_index: int,
    traversal_had_lines: bool,
    max_lines: int,
    filter_strings: List[str],
    reverse: bool,
    default_log_info_message: Optional[str] = None,
) -> LogLineResult:
    """Load the lines for runs that are NOT inline."""
    prefix = log_prefix(run_id, JobKind.run)
    latest_log_file = _get_latest_log_file(prefix, cursor_file)
    if latest_log_file is None:
        return LogLineResult(
            can_continue_forward=still_running,
            can_continue_backward=False,
            lines=[],
            line_ids=[],
            forward_cursor_token=Cursor.nothing_found(
                filter_strings, run_id, reverse=False
            ).to_token()
            if still_running
            else None,
            reverse_cursor_token=None,
            log_info_message="No log files found",
        )
    line_stream = line_stream_from_log_directory(
        prefix,
        cursor_file=cursor_file,
        cursor_line_index=cursor_line_index,
        reverse=reverse,
    )

    return get_log_lines_from_line_stream(
        line_stream=line_stream,
        still_running=still_running,
        traversal_had_lines=traversal_had_lines,
        max_lines=max_lines,
        filter_strings=filter_strings,
        run_id=run_id,
        default_log_info_message=default_log_info_message,
        cursor_file=cursor_file,
        cursor_line_index=cursor_line_index,
        reverse=reverse,
    )


def _load_inline_logs(
    run_id: str,
    resolution: Resolution,
    still_running: bool,
    cursor_file: Optional[str],
    cursor_line_index: int,
    traversal_had_lines: bool,
    max_lines: int,
    filter_strings: List[str],
    default_log_info_message: Optional[str] = None,
    reverse: bool = False,
) -> LogLineResult:
    """Load the lines for runs that are inline."""

    if ResolutionKind[resolution.kind] == ResolutionKind.LOCAL:  # type: ignore
        return LogLineResult(
            can_continue_forward=False,
            can_continue_backward=False,
            lines=[],
            line_ids=[],
            forward_cursor_token=None,
            reverse_cursor_token=None,
            log_info_message=(
                "UI logs are only available for runs that "
                "(a) are executed using the CloudResolver and "
                "(b) are using the resolver in non-detached mode OR have standalone=True."
            ),
        )

    prefix = log_prefix(resolution.root_id, JobKind.resolver)
    latest_log_file = _get_latest_log_file(prefix, cursor_file)
    if latest_log_file is None:
        return LogLineResult(
            can_continue_forward=still_running,
            can_continue_backward=False,
            forward_cursor_token=Cursor.nothing_found(
                filter_strings, run_id, reverse=False
            ).to_token()
            if still_running
            else None,
            reverse_cursor_token=None,
            lines=[],
            line_ids=[],
            log_info_message="Resolver logs are missing",
        )

    prefix = log_prefix(resolution.root_id, JobKind.resolver)
    line_stream = line_stream_from_log_directory(
        prefix,
        cursor_file=cursor_file,
        cursor_line_index=cursor_line_index,
        reverse=reverse,
    )
    line_stream = _filter_for_inline(
        line_stream=line_stream,
        run_id=run_id,
        # we already found the indicator for the inline run start with the current cursor
        skip_start=traversal_had_lines,
        reverse=reverse,
    )

    return get_log_lines_from_line_stream(
        line_stream=line_stream,
        still_running=still_running,
        traversal_had_lines=traversal_had_lines,
        max_lines=max_lines,
        filter_strings=filter_strings,
        run_id=run_id,
        cursor_file=cursor_file,
        cursor_line_index=cursor_line_index,
        default_log_info_message=default_log_info_message,
        reverse=reverse,
    )


def line_stream_from_log_directory(
    directory: str,
    cursor_file: Optional[str],
    cursor_line_index: Optional[int],
    reverse: bool,
) -> Iterable[LogLine]:
    """Stream lines from multiple files in a storage dir, starting from cursor."""
    storage_class = get_storage_plugins([LocalStorage])[0]

    storage = storage_class()

    log_files = storage.get_child_paths(directory)

    log_files = sorted(
        log_files,
        key=lambda path_key: int(
            path_key.replace(directory, "").replace(".log", "".replace("/", ""))
        ),
        reverse=reverse,
    )
    if len(log_files) == 0:
        yield from []
        return
    index_of_log_file = 0
    if cursor_file is not None:
        if cursor_file not in log_files:
            raise ValueError(f"Cursor referenced invalid log file {cursor_file}.")
        index_of_log_file = log_files.index(cursor_file)

    cursor_file = log_files[index_of_log_file]
    log_files_to_traverse = log_files[index_of_log_file:]
    for log_file in log_files_to_traverse:
        start_line_index = DEFAULT_END_INDEX if reverse else DEFAULT_START_INDEX
        if log_file == cursor_file and cursor_line_index is not None:
            start_line_index = cursor_line_index

        text_stream: Iterable[str] = storage.get_line_stream(log_file)
        yield from _stream_from_text_stream_from_index(
            log_file, start_line_index, reverse, text_stream
        )


def _stream_from_text_stream_from_index(
    log_file: str, start_line_index: int, reverse: bool, text_stream: Iterable[str]
) -> Iterable[LogLine]:
    """Starting at the given index within the file, stream logs in desired direction.

    When going forward, the line pointed to by the index will be included. When going in
    the reverse direction, the line pointed to by the index will be omitted.
    """
    # For purposes of this function, "preceding" refers to indices
    # lower than the start index, regardless of traversal direction.
    lines_preceding_cursor: List[LogLine] = []
    if reverse:
        for i_line, line in enumerate(text_stream):
            as_log_line = LogLine(
                source_file=log_file,
                source_file_index=i_line,
                line=line,
            )
            if i_line < start_line_index:
                lines_preceding_cursor.append(as_log_line)
            else:
                # once we hit the cursor, we have everything we
                # need to go backwards
                break

        yield from reversed(lines_preceding_cursor)
    else:
        for i_line, line in enumerate(text_stream):
            as_log_line = LogLine(
                source_file=log_file,
                source_file_index=i_line,
                line=line,
            )
            if i_line < start_line_index:
                continue
            yield as_log_line


def _filter_for_inline(
    line_stream: Iterable[LogLine], run_id: str, skip_start: bool, reverse: bool
) -> Iterable[LogLine]:
    """Stream resolver logs to make a new stream with only lines for a particular run."""
    if reverse:
        expected_start = END_INLINE_RUN_INDICATOR.format(run_id)
        expected_end = START_INLINE_RUN_INDICATOR.format(run_id)
    else:
        expected_start = START_INLINE_RUN_INDICATOR.format(run_id)
        expected_end = END_INLINE_RUN_INDICATOR.format(run_id)
    buffer_iterator = iter(line_stream)
    found_start = skip_start
    while True:
        try:
            log_line: LogLine = next(buffer_iterator)
        except StopIteration:
            # if a resolver dies mid-execution of an inline run,
            # we should treat the end of the existing lines as
            # the end of whatever inline we were looking for.
            break
        if expected_start in log_line.line:
            found_start = True
            continue
        if not found_start:
            continue
        if expected_end in log_line.line:
            break
        yield log_line


def get_log_lines_from_line_stream(
    line_stream: Iterable[LogLine],
    still_running: bool,
    traversal_had_lines: bool,
    max_lines: int,
    filter_strings: List[str],
    run_id: str,
    cursor_file: Optional[str] = None,
    cursor_line_index: Optional[int] = None,
    default_log_info_message: Optional[str] = None,
    reverse: bool = False,
) -> LogLineResult:
    """Given a stream of log lines, produce an object containing the desired subset

    Parameters
    ----------
    line_stream:
        An iterable stream of log lines
    still_running:
        A boolean indicating whether the run these logs are for is still running or not
    traversal_had_lines:
        Has the traversal this cursor is continuing contained any lines?
    max_lines:
        The maximum number of lines that should be returned
    filter_strings:
        A list of strings to filter log lines by. Only log lines that contain ALL the
        filters will be returned.
    run_id:
        The id of the run the traversal is for.
    cursor_file:
        The file of the cursor in the current direction, if continuing from a cursor.
    cursor_line_index:
        The line index of the cursor in the current direction, if continuing from a
        cursor.
    default_log_info_message:
        A default extra log info message to provide the user, unless a specific one needs
        to be provided.
    reverse:
        Whether the log lines are being traversed in reverse order.

    Returns
    -------
    A subset of the logs for the given run
    """
    original_cursor_file = cursor_file
    original_cursor_line_index = cursor_line_index
    buffer_iterator = iter(line_stream)
    keep_going = True
    lines: List[str] = []
    line_ids: List[int] = []

    def passes_filter(line: LogLine) -> bool:
        return all(substring in line.line for substring in filter_strings)

    # "earliest" and "latest" here refer to chronological
    # line order, not iteration order.
    earliest_included_line_file = None
    earliest_included_line_index = None
    latest_included_line_file = None
    latest_included_line_index = None
    while keep_going:
        try:
            # For reverse direction, these lines are being iterated in
            # reverse chronological order.
            line = next(ln for ln in buffer_iterator)
            if not passes_filter(line):
                continue

            if reverse:
                if latest_included_line_index is None:
                    latest_included_line_file = line.source_file
                    latest_included_line_index = line.source_file_index
                earliest_included_line_file = line.source_file
                earliest_included_line_index = line.source_file_index
            else:
                if earliest_included_line_index is None:
                    earliest_included_line_file = line.source_file
                    earliest_included_line_index = line.source_file_index
                latest_included_line_file = line.source_file
                latest_included_line_index = line.source_file_index

            lines.append(line.line)
            line_ids.append(to_line_id(line.source_file, line.source_file_index))
            if len(lines) >= max_lines:
                keep_going = False
        except StopIteration:
            keep_going = False

    # recall: in the forward direction, when starting from a cursor, the
    # line pointed to by the cursor is *included*. In the reverse direction,
    # the line pointed to by the cursor is *omitted*.

    # Forward cursor should be AFTER the latest included line.
    # Reverse one should be AT the earliest included line.
    forward_cursor_file = latest_included_line_file
    forward_cursor_index: Optional[int] = (
        latest_included_line_index + 1
        if latest_included_line_index is not None
        else None
    )
    reverse_cursor_file = earliest_included_line_file
    reverse_cursor_index = earliest_included_line_index
    if reverse_cursor_file is None and len(lines) == 0 and not reverse:
        # Empty forward traversal. Might still be able to continue
        # backwards from where the forward cursor was originally
        # pointing even if we found nothing in forward direction.
        reverse_cursor_file = original_cursor_file
        reverse_cursor_index = original_cursor_line_index
    if forward_cursor_file is None and len(lines) == 0 and reverse:
        # Empty reverse traversal. Might still be able to continue
        # forwards from where the reverse cursor was originally
        # pointing even if we found nothing in reverse direction.
        forward_cursor_file = original_cursor_file
        forward_cursor_index = original_cursor_line_index

    if still_running and forward_cursor_file is None and not reverse:
        # No new lines have been found, but run is still running. So
        # we might get more if we try the same cursor again after waiting.
        forward_cursor_file = original_cursor_file
        forward_cursor_index = original_cursor_line_index

    forward_cursor_token = None
    reverse_cursor_token = None
    if forward_cursor_file is not None:
        if reverse or (len(lines) == max_lines or still_running):
            forward_cursor_token = Cursor(
                source_log_key=forward_cursor_file,
                source_file_line_index=forward_cursor_index,  # type: ignore
                filter_strings=filter_strings,
                run_id=run_id,
                traversal_had_lines=traversal_had_lines or len(lines) > 0,
                reverse=False,
            ).to_token()
    if reverse_cursor_file is not None:
        if not reverse or len(lines) == max_lines:
            reverse_cursor_token = Cursor(
                source_log_key=reverse_cursor_file,
                source_file_line_index=reverse_cursor_index,  # type: ignore
                filter_strings=filter_strings,
                run_id=run_id,
                traversal_had_lines=traversal_had_lines or len(lines) > 0,
                reverse=True,
            ).to_token()

    log_info_message = (
        default_log_info_message if len(lines) > 0 else "No matching log lines."
    )

    return LogLineResult(
        can_continue_forward=forward_cursor_token is not None,
        can_continue_backward=reverse_cursor_token is not None,
        lines=list(reversed(lines)) if reverse else lines,
        line_ids=list(reversed(line_ids)) if reverse else line_ids,
        forward_cursor_token=forward_cursor_token,
        reverse_cursor_token=reverse_cursor_token,
        log_info_message=log_info_message,
    )


T = TypeVar("T")


def reversed(iterable: Iterable[T]) -> Iterable[T]:
    """Return an iterator over the elements in the reverse order.

    Differs from built-in `reversed` in that it works with generators,
    and materializes the whole iterator in memory before reversing.
    It is thus unsuitable for large/infitnite iterables.
    """
    as_list = []
    for item in iterable:
        as_list.append(item)
    as_list.reverse()
    yield from as_list


def to_line_id(log_file: str, line_index: int) -> int:
    """Get a unique id for each log line.

    Line ids are only guaranteed unique within a given run or resolver
    execution. However, within such a context, the line ids are in
    chronological order. Some line ids may appear to be sequential with
    no gap, but it is not guaranteed that there will be no gaps between ids.

    It should only be used for actual lines, and not abstract positions (such as
    cursors).

    Callers should not depend on any details about how this id is constructed.

    Parameters
    ----------
    log_file:
        The name of the log file where the line occurs.
    line_index:
        The index of the line within the log file.
    """
    timestamp = int("".join(char for char in log_file.split("/")[-1] if char.isdigit()))

    # obfuscate the fact that there's a timestamp here; we don't want the
    # front-end to actually use it as such. It only represents the time
    # the whole *log file* was ingested, and not when any individual line
    # was.
    prefix = timestamp - 1500000000000

    # We know the suffix will be less than MAX_LINES_PER_LOG_FILE. However,
    # that limit was fairly recent so we can use an extra 0 to be safe.
    # For logs older than the MAX_LINES_PER_LOG_FILE rule, timestamps
    # would be 10 seconds apart and the timestamps are in milliseconds,
    # which gives us more headroom to avoid duplication.
    suffix = line_index
    return 10 * MAX_LINES_PER_LOG_FILE * prefix + suffix
