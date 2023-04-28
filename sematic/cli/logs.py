# Standard Library
import logging
import sys
import time

# Third-party
import click

# Sematic
from sematic import api_client
from sematic.cli.cli import advanced, cli
from sematic.config.config import get_config, switch_env
from sematic.log_reader import (
    ObjectSource,
    line_stream_from_log_directory,
    load_log_lines,
)

DEFAULT_LOG_LOAD_MAX_SIZE = 1000


@cli.command("logs", short_help="Read logs for a run")
@click.option("-f", "--follow", default=False, is_flag=True)
@click.argument("run_id", type=click.STRING)
def logs(run_id: str, follow: bool):
    """Read the logs for the run directly from blob storage, and print to stdout.

    If the run is still producing logs, this will follow the logs "live" until
    no more log lines are being produced.
    """
    switch_env("user")  # only makes sense for this env

    # Don't want Sematic logs interfering with the ones being pulled
    # from the remote
    logging.basicConfig(level=logging.ERROR)

    try:
        api_client.get_run(run_id)
    except api_client.ResourceNotFoundError:
        click.secho(
            f"Could not find run with id '{run_id}' at {get_config().api_url}.",
            fg="red",
        )
        sys.exit(1)

    has_more = True
    cursor = None
    had_any = False

    while has_more:
        loaded = load_log_lines(
            run_id,
            forward_cursor_token=cursor,
            reverse_cursor_token=None,
            max_lines=DEFAULT_LOG_LOAD_MAX_SIZE,
            filter_strings=None,
            object_source=ObjectSource.API,
        )
        has_more = loaded.can_continue_forward

        if len(loaded.lines) == 0:

            if not (had_any or has_more):
                click.secho(loaded.log_info_message, fg="red")
                sys.exit(1)
            if not follow:
                break

            # give storage API a quick break while we wait for some logs to appear
            time.sleep(1)
            continue

        cursor = loaded.forward_cursor_token

        for line in loaded.lines:
            had_any = True
            click.echo(line)


@advanced.command(
    "dump-log-storage", short_help="Dumps all logs in a blob storage directory"
)
@click.argument("storage_key", type=click.STRING)
def dump_log_storage(storage_key: str):
    """Dumps all logs stored in a blob storage directory.

    The logs will be concatenated and dumped to stdout. Logs will not be
    "followed;" whatever logs are present at the time the dump is initiated
    will be dumped and the command will exit.

    This is useful primarily for infrastructure debugging purposes, such as
    to dump the full logs for a resolution
    (ex: logs/v2/run_id/{resolution_id}/driver/).
    It does not require API access, only storage access.
    """

    # Don't want Sematic logs interfering with the ones being pulled
    # from the remote
    logging.basicConfig(level=logging.ERROR)
    storage_key = storage_key if storage_key.endswith("/") else f"{storage_key}/"
    line_stream = line_stream_from_log_directory(
        storage_key,
        cursor_file=None,
        cursor_line_index=None,
        reverse=False,
    )
    found_lines = False

    for log_line in line_stream:
        found_lines = True
        print(log_line.line)

    if not found_lines:
        click.secho(f"No logs found in storage at '{storage_key}'", fg="red")
        sys.exit(1)
