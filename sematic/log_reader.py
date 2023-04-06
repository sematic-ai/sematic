# Standard Library
import base64
import json
import logging
from dataclasses import asdict, dataclass
from enum import Enum, unique
from typing import Iterable, List, Optional

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
from sematic.scheduling.job_details import JobKind, JobKindString

V2_LOG_PREFIX = "logs/v2"
LOG_PATH_FORMAT = "{prefix}/run_id/{run_id}/{log_kind}/"

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
    more_before:
        Are there more lines before the first line returned?
    more_after:
        Are there more lines after the last line returned? Will be True
        if the answer is known to be yes, False if the answer is known to
        be no. If the answer is not known (i.e. run may still be in
        progress), True will be returned.
    lines:
        The actual log lines
    continuation_cursor:
        A string that can be used to continue traversing these logs from where you left
        off. If more_after is False, this will be set to None.
    log_info_message:
        A human-readable extra info message.
    """

    more_before: bool
    more_after: bool
    lines: List[str]
    continuation_cursor: Optional[str]
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
        It will be the first line that HASN'T yet been read. If no logs have been found,
        will be -1.
    filter_strings:
        The filter strings that were used for this log traversal.
    run_id:
        The run id that was being used for this log traversal.
    traversal_had_lines:
        Will be True if this cursor corresponds to a result that has lines, or
        if it continues from a chain of cursors that had found some lines
    """

    source_log_key: Optional[str]
    source_file_line_index: int
    filter_strings: List[str]
    run_id: str
    traversal_had_lines: bool = False

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
    def nothing_found(cls, filter_strings: List[str], run_id: str):
        return Cursor(
            source_log_key=None,
            source_file_line_index=-1,
            filter_strings=filter_strings,
            run_id=run_id,
            traversal_had_lines=False,
        )


@dataclass
class LogLine:
    source_file: str
    source_file_index: int
    line: str


def load_log_lines(
    run_id: str,
    continuation_cursor: Optional[str],
    max_lines: int,
    filter_strings: Optional[List[str]] = None,
    object_source: ObjectSource = ObjectSource.DB,
) -> LogLineResult:
    """Load a portion of the logs for a particular run.

    Parameters
    ----------
    run_id:
        The id of the run to get logs for
    continuation_cursor:
        A cursor indicating where to continue reading logs from. Should be
        None if the logs are being read from the beginning.
    max_lines:
        The highest number of log lines that should be returned at once
    filter_strings:
        Only log lines that contain ALL the strings in this list will
        be included in the result
    object_source:
        How to get runs/resolutions

    Returns
    -------
    A subset of the logs for the given run
    """
    logger.info(
        "Starting log line loading for: %s, %s, %s, %s",
        run_id,
        continuation_cursor,
        max_lines,
        filter_strings,
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
    cursor = (
        Cursor.from_token(continuation_cursor)
        if continuation_cursor is not None
        else Cursor.nothing_found(filter_strings, run_id)
    )

    if cursor.run_id != run_id:
        raise ValueError(
            f"Tried to continue a log search of {run_id} using a "
            f"continuation cursor from {cursor.run_id}"
        )
    if set(cursor.filter_strings) != set(filter_strings):
        raise ValueError(
            f"Tried to continue a log search of {run_id} using a "
            f"different set of filters than were used in the cursor."
        )

    if ResolutionStatus[resolution.status] in (  # type: ignore
        ResolutionStatus.CREATED,
        ResolutionStatus.SCHEDULED,
    ):
        return LogLineResult(
            more_before=False,
            more_after=True,
            lines=[],
            continuation_cursor=cursor.to_token(),
            log_info_message="Resolution has not started yet.",
        )

    filter_strings = filter_strings if filter_strings is not None else []
    if FutureState[run.future_state] == FutureState.CREATED:  # type: ignore
        return LogLineResult(
            more_before=False,
            more_after=True,
            lines=[],
            continuation_cursor=cursor.to_token(),
            log_info_message="The run has not yet started executing.",
        )

    is_inline = object_source.run_is_inline(run.id)
    if is_inline:
        return _load_inline_logs(
            run_id=run_id,
            resolution=resolution,
            still_running=still_running,
            cursor_file=cursor.source_log_key,
            cursor_line_index=cursor.source_file_line_index,
            cursor_had_more_before=cursor.traversal_had_lines,
            max_lines=max_lines,
            filter_strings=filter_strings,
            default_log_info_message=default_log_info_message,
        )

    return _load_non_inline_logs(
        run_id=run_id,
        still_running=still_running,
        cursor_file=cursor.source_log_key,
        cursor_line_index=cursor.source_file_line_index,
        cursor_had_more_before=cursor.traversal_had_lines,
        max_lines=max_lines,
        filter_strings=filter_strings,
        default_log_info_message=default_log_info_message,
    )


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
    cursor_had_more_before: bool,
    max_lines: int,
    filter_strings: List[str],
    default_log_info_message: Optional[str] = None,
) -> LogLineResult:
    """Load the lines for runs that are NOT inline."""
    prefix = log_prefix(run_id, JobKind.run)
    latest_log_file = _get_latest_log_file(prefix, cursor_file)
    if latest_log_file is None:
        return LogLineResult(
            more_before=False,
            more_after=still_running,
            lines=[],
            continuation_cursor=Cursor.nothing_found(filter_strings, run_id).to_token()
            if still_running
            else None,
            log_info_message="No log files found",
        )
    line_stream = line_stream_from_log_directory(
        prefix, cursor_file=cursor_file, cursor_line_index=cursor_line_index
    )

    return get_log_lines_from_line_stream(
        line_stream=line_stream,
        still_running=still_running,
        cursor_source_file=cursor_file,
        cursor_line_index=cursor_line_index,
        cursor_had_more_before=cursor_had_more_before,
        max_lines=max_lines,
        filter_strings=filter_strings,
        run_id=run_id,
        default_log_info_message=default_log_info_message,
    )


def _load_inline_logs(
    run_id: str,
    resolution: Resolution,
    still_running: bool,
    cursor_file: Optional[str],
    cursor_line_index: int,
    cursor_had_more_before: bool,
    max_lines: int,
    filter_strings: List[str],
    default_log_info_message: Optional[str] = None,
) -> LogLineResult:
    """Load the lines for runs that are inline."""

    if ResolutionKind[resolution.kind] == ResolutionKind.LOCAL:  # type: ignore
        return LogLineResult(
            more_before=False,
            more_after=False,
            lines=[],
            continuation_cursor=None,
            log_info_message=(
                "UI logs are only available for runs that "
                "(a) are executed using the CloudResolver and "
                "(b) are using the resolver in non-detached mode OR have inline=False."
            ),
        )

    prefix = log_prefix(resolution.root_id, JobKind.resolver)
    latest_log_file = _get_latest_log_file(prefix, cursor_file)
    if latest_log_file is None:
        return LogLineResult(
            more_before=False,
            more_after=still_running,
            continuation_cursor=Cursor.nothing_found(filter_strings, run_id).to_token()
            if still_running
            else None,
            lines=[],
            log_info_message="Resolver logs are missing",
        )

    prefix = log_prefix(resolution.root_id, JobKind.resolver)
    line_stream = line_stream_from_log_directory(
        prefix, cursor_file=cursor_file, cursor_line_index=cursor_line_index
    )
    line_stream = _filter_for_inline(
        line_stream=line_stream,
        run_id=run_id,
        # we already found the indicator for the inline run start with the current cursor
        skip_start=cursor_had_more_before,
    )

    return get_log_lines_from_line_stream(
        line_stream=line_stream,
        still_running=still_running,
        cursor_source_file=cursor_file,
        cursor_line_index=cursor_line_index,
        cursor_had_more_before=cursor_had_more_before,
        max_lines=max_lines,
        filter_strings=filter_strings,
        run_id=run_id,
        default_log_info_message=default_log_info_message,
    )


def line_stream_from_log_directory(
    directory: str, cursor_file: Optional[str], cursor_line_index: Optional[int]
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
    )
    found_cursor_file = cursor_file is None
    found_cursor_line = cursor_line_index is None
    for log_file in log_files:
        if log_file == cursor_file:
            found_cursor_file = True
        if not found_cursor_file:
            continue
        text_stream: Iterable[str] = storage.get_line_stream(log_file)
        for i_line, line in enumerate(text_stream):
            if (
                (not found_cursor_line)
                and cursor_line_index is not None
                and i_line < cursor_line_index
            ):
                continue
            found_cursor_line = True
            yield LogLine(
                source_file=log_file,
                source_file_index=i_line,
                line=line,
            )
        if cursor_file is not None and log_file >= cursor_file:
            # we automatically know we hit the cursor line if we are at the end
            # of the cursor file or in a file that comes after it.
            found_cursor_line = True


def _filter_for_inline(
    line_stream: Iterable[LogLine], run_id: str, skip_start: bool
) -> Iterable[LogLine]:
    """Stream resolver logs to make a new stream with only lines for a particular run."""
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
    cursor_source_file: Optional[str],
    cursor_line_index: int,
    cursor_had_more_before: bool,
    max_lines: int,
    filter_strings: List[str],
    run_id: str,
    default_log_info_message: Optional[str] = None,
) -> LogLineResult:
    """Given a stream of log lines, produce an object containing the desired subset

    Parameters
    ----------
    line_stream:
        An iterable stream of log lines
    still_running:
        A boolean indicating whether the run these logs are for is still running or not
    cursor_source_file:
        The source file to continue from. No lines should be returned until this file is
        reached.
    cursor_line_index:
        The source file to continue from. No lines should be returned until this source
        file index is reached.
    cursor_had_more_before:
        Whether the cursor had matching lines before it
    max_lines:
        The maximum number of lines that should be returned
    filter_strings:
        A list of strings to filter log lines by. Only log lines that contain ALL the
        filters will be returned.
    run_id:
        The id of the run the traversal is for.
    default_log_info_message:
        A default extra log info message to provide the user, unless a specific one needs
        to be provided.

    Returns
    -------
    A subset of the logs for the given run
    """
    buffer_iterator = iter(line_stream)
    keep_going = True
    lines = []
    has_more = True
    more_before = cursor_had_more_before
    source_file = None
    source_file_line_index = -1
    found_cursor = False

    def passes_filter(line: LogLine) -> bool:
        return all(substring in line.line for substring in filter_strings)

    while keep_going:
        try:
            line = next(ln for ln in buffer_iterator)
            source_file = line.source_file
            source_file_line_index = line.source_file_index

            if not found_cursor:
                if (
                    cursor_source_file is None
                    or source_file > cursor_source_file
                    or source_file == cursor_source_file
                    and source_file_line_index >= cursor_line_index
                ):
                    found_cursor = True
                else:
                    more_before = more_before or passes_filter(line)
                    continue

            if not passes_filter(line):
                continue

            lines.append(line.line)

            if len(lines) >= max_lines:
                has_more = True
                keep_going = False
        except StopIteration:
            keep_going = False

            # hit the end of the logs produced so far. If the run is done,
            # there are no more logs. Otherwise, more might show up!
            has_more = still_running

    if not has_more:
        cursor_token = None
    elif found_cursor:
        cursor_token = Cursor(
            source_log_key=source_file,
            # +1: next time we want to start AFTER where we last read
            source_file_line_index=source_file_line_index + 1,
            filter_strings=filter_strings,
            run_id=run_id,
            traversal_had_lines=more_before or len(lines) > 0,
        ).to_token()
    else:
        # didn't find anything new, just use the existing cursor values
        cursor_token = Cursor(
            source_log_key=cursor_source_file,
            source_file_line_index=cursor_line_index,
            filter_strings=filter_strings,
            run_id=run_id,
            traversal_had_lines=cursor_had_more_before,
        ).to_token()

    log_info_message = (
        default_log_info_message if len(lines) > 0 else "No matching log lines."
    )

    return LogLineResult(
        more_before=more_before,
        more_after=has_more,
        lines=lines,
        continuation_cursor=cursor_token,
        log_info_message=log_info_message,
    )
