# Standard Library
from dataclasses import dataclass
from typing import Iterable, List, Optional

# Sematic
from sematic import storage
from sematic.abstract_future import FutureState
from sematic.db.models.resolution import Resolution, ResolutionKind, ResolutionStatus
from sematic.db.queries import get_resolution, get_run
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
    filter_strings: Optional[List[str]] = None,
) -> LogLineResult:
    run = get_run(run_id)
    run_state = FutureState[run.future_state]  # type: ignore
    still_running = run_state.is_terminal() or run_state == FutureState.RAN
    resolution = get_resolution(run.root_id)
    if ResolutionStatus[resolution.status] in (  # type: ignore
        ResolutionStatus.CREATED,
        ResolutionStatus.SCHEDULED,
    ):
        return LogLineResult(
            start_index=-1,
            end_index=-1,
            more_before=False,
            more_after=True,
            lines=[],
            log_unavaiable_reason="Resolution has not started yet.",
        )
    filter_strings = filter_strings if filter_strings is not None else []
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
            run_id=run_id,
            resolution=resolution,
            still_running=still_running,
            first_line_index=first_line_index,
            max_lines=max_lines,
            filter_strings=filter_strings,
        )
    return _load_non_inline_logs(
        run_id=run_id,
        still_running=still_running,
        first_line_index=first_line_index,
        max_lines=max_lines,
        filter_strings=filter_strings,
    )


def _load_non_inline_logs(
    run_id: str,
    still_running: bool,
    first_line_index: int,
    max_lines: int,
    filter_strings: List[str],
) -> LogLineResult:
    prefix = log_prefix(run_id, is_resolve=False)
    log_files = storage.get_child_paths(prefix)
    if len(log_files) < 1:
        return LogLineResult(
            start_index=-1,
            end_index=-1,
            more_before=False,
            more_after=True,
            lines=[],
            log_unavaiable_reason="No log files found",
        )

    # the file wth the highest timestamp has the full logs.
    latest_log_file = max(
        log_files,
        key=lambda path_key: int(
            path_key.replace(prefix, "").replace(".log", "".replace("/", ""))
        ),
    )
    text_buffer = storage.get_line_stream(latest_log_file)

    return get_log_lines_from_text_buffer(
        text_buffer, still_running, first_line_index, max_lines, filter_strings
    )


def _load_inline_logs(
    run_id: str,
    resolution: Resolution,
    still_running: bool,
    first_line_index: int,
    max_lines: int,
    filter_strings: List[str],
) -> LogLineResult:
    if ResolutionKind[resolution.kind] == ResolutionKind.LOCAL:  # type: ignore
        return LogLineResult(
            start_index=-1,
            end_index=-1,
            more_before=False,
            more_after=True,
            lines=[],
            log_unavaiable_reason=(
                "UI logs are only available for runs that "
                "(a) are executed using the CloudResolver and "
                "(b) are using the resolver in non-detached mode OR have inline=False."
            ),
        )
    log_files = storage.get_child_paths(log_prefix(resolution.root_id, is_resolve=True))
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

    text_buffer: Iterable[str] = storage.get_line_stream(latest_log_file)
    text_buffer = _filter_for_inline(text_buffer, run_id)

    return get_log_lines_from_text_buffer(
        text_buffer, still_running, first_line_index, max_lines, filter_strings
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
    still_running: bool,
    first_line_index: int,
    max_lines: int,
    filter_strings: List[str],
) -> LogLineResult:
    buffer_iterator = iter(text_buffer)
    keep_going = True
    current_index = 0
    lines = []
    has_more = True
    more_before = False
    first_read_index = -1

    def passes_filter(line) -> bool:
        return all(substring in line for substring in filter_strings)

    while keep_going:
        try:
            line = next(ln for ln in buffer_iterator if passes_filter(ln))
            if current_index >= first_line_index:
                if first_read_index < 0:
                    first_read_index = current_index
                lines.append(line)
            else:
                more_before = True
            current_index += 1
            if len(lines) >= max_lines:
                has_more = True
                keep_going = False
        except StopIteration:
            keep_going = False

            # hit the end of the logs produced so far. If the run is
            # done, there are no more logs. Otherwise more might show
            # up!
            has_more = still_running
    missing_reason = None if len(lines) > 0 else "No matching log lines."
    return LogLineResult(
        start_index=first_read_index,
        end_index=current_index,
        more_before=more_before,
        more_after=has_more,
        lines=lines,
        log_unavaiable_reason=missing_reason,
    )
