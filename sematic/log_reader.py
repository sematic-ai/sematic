# Standard Library
import io
from dataclasses import dataclass
from typing import Iterable, List, Optional

# Sematic
from sematic import storage
from sematic.abstract_future import FutureState
from sematic.db.queries import get_run
from sematic.resolvers.cloud_resolver import (
    END_INLINE_RUN_INDICATOR,
    START_INLINE_RUN_INDICATOR,
)

V1_LOG_PATH_FORMAT = "logs/v1/run_id/{run_id}/{log_kind}/"


def log_prefix(run_id: str, is_resolve: bool):
    kind = "resolve" if is_resolve else "calculation"
    return V1_LOG_PATH_FORMAT.format(run_id=run_id, log_kind=kind)


@dataclass
class LogLineResult:
    """Results of a query for log lines

    Indexes are given as positive numbers from the start of the logs.
    Line 0 is the first line. Line 1 is the next one, etc.. If the index
    is negative, that means no logs are available.

    If lines are filtered, the indices refer to the logs as they are AFTER
    the filter is applied.

    Attributes
    ----------
    start_index:
        The index of the earliest log line in the result
    end_index:
        The index AFTER the latest log line in the result.
    more_before:
        Are there more lines before the first line returned?
    more_after:
        Are there more lines after the last line returned? Will be True
        if the answer is known to be yes, False if the answer is known to
        be no. If the answer is not known (i.e. run may still be in
        progress), True will be returned.
    lines:
        The actual log lines
    log_unavaiable_reason:
        A human-readable reason why logs are not available.
    """

    start_index: int
    end_index: int
    more_before: bool
    more_after: bool
    lines: List[str]
    log_unavaiable_reason: Optional[str] = None


def load_log_lines(
    run_id: str,
    first_line_index: int,
    max_lines: int,
    filter_string: Optional[str] = None,
) -> LogLineResult:
    run = get_run(run_id)
    filter_string = filter_string if filter_string is not None else ""
    if FutureState[run.future_state] == FutureState.CREATED:  # type: ignore
        return LogLineResult(
            start_index=-1,
            end_index=-1,
            more_before=False,
            more_after=True,
            lines=[],
            log_unavaiable_reason="The run has not yet started executing.",
        )
    # looking for external jobs to determine inline is only valid
    # since we know the run has at least reached SCHEDULED due to it
    # not being CREATED.
    is_inline = len(run.external_jobs) == 0
    if is_inline:
        return _load_inline_logs(
            run_id, run.root_id, first_line_index, max_lines, filter_string
        )
    return _load_non_inline_logs(run_id, first_line_index, max_lines, filter_string)


def _load_non_inline_logs(
    run_id: str, first_line_index: int, max_lines: int, filter_string: str
) -> LogLineResult:
    log_files = storage.get_child_paths(log_prefix(run_id, is_resolve=False))
    if len(log_files) < 1:
        return LogLineResult(
            start_index=-1,
            end_index=-1,
            more_before=False,
            more_after=True,
            lines=[],
            log_unavaiable_reason="No log files found.",
        )

    # the file wth the highest timestamp has the full logs.
    latest_log_file = max(log_files)

    buffer = io.BytesIO()
    storage.get_stream(latest_log_file, buffer)
    text_buffer = io.TextIOWrapper(buffer, encoding="utf8")
    return get_log_lines_from_text_buffer(
        text_buffer, first_line_index, max_lines, filter_string
    )


def _load_inline_logs(
    run_id: str, root_id: str, first_line_index: int, max_lines: int, filter_string: str
) -> LogLineResult:
    log_files = storage.get_child_paths(log_prefix(root_id, is_resolve=True))
    if len(log_files) < 1:
        return LogLineResult(
            start_index=-1,
            end_index=-1,
            more_before=False,
            more_after=True,
            lines=[],
            log_unavaiable_reason="Resolver logs are missing",
        )

    # the file wth the highest timestamp has the full logs.
    latest_log_file = max(log_files)

    buffer = io.BytesIO()
    storage.get_stream(latest_log_file, buffer)
    text_buffer: Iterable[str] = io.TextIOWrapper(buffer, encoding="utf8")
    text_buffer = _filter_for_inline(text_buffer, run_id)

    return get_log_lines_from_text_buffer(
        text_buffer, first_line_index, max_lines, filter_string
    )


def _filter_for_inline(text_buffer: Iterable[str], run_id: str) -> Iterable[str]:
    expected_start = START_INLINE_RUN_INDICATOR.format(run_id)
    expected_end = END_INLINE_RUN_INDICATOR.format(run_id)
    buffer_iterator = iter(text_buffer)
    found_start = False
    while True:
        line = next(buffer_iterator)
        if expected_start in line:
            found_start = True
            continue
        if not found_start:
            continue
        if expected_end in line:
            break
        yield line


def get_log_lines_from_text_buffer(
    text_buffer: Iterable[str],
    first_line_index: int,
    max_lines: int,
    filter_string: str,
) -> LogLineResult:
    buffer_iterator = iter(text_buffer)
    keep_going = True
    current_index = 0
    lines = []
    has_more = True
    more_before = False
    first_read_index = -1
    while keep_going:
        try:
            line = next(ln for ln in buffer_iterator if filter_string in ln)
            if first_line_index <= current_index:
                if first_line_index < 0:
                    first_read_index = current_index
                lines.append(line)
            else:
                more_before = True
            current_index += 1
            if current_index >= max_lines:
                has_more = True
                keep_going = False
        except StopIteration:
            keep_going = False
            has_more = False
    return LogLineResult(
        start_index=first_read_index,
        end_index=current_index,
        more_before=more_before,
        more_after=has_more,
        lines=lines,
    )
