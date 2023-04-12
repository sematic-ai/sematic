# Standard Library
import logging
import os
from logging.config import dictConfig

# Third-party
import click

# Sematic
from sematic.api.endpoints.auth import get_cleaner_api_key

# TODO: will use API client to perform cleaning operations
# import sematic.api_client as api_client
from sematic.cli.cli import cli
from sematic.config.user_settings import UserSettingsVar
from sematic.logging import make_log_config

logger = logging.getLogger(__name__)


@cli.command("clean", short_help="Clean up orphaned resources")
@click.option(
    "--orphaned-jobs",
    is_flag=True,
    show_default=True,
    default=False,
    help="Clean jobs whose associated runs have stopped.",
)
@click.option(
    "--orphaned-resources",
    is_flag=True,
    show_default=True,
    default=False,
    help="Clean up external resources (ex: Ray clusters) whose runs have stopped.",
)
def clean(orphaned_jobs: bool, orphaned_resources: bool):
    """
    Clean up objects that are no longer be needed.
    """
    running_as_cron_job = os.environ.get("RUNNING_AS_CRON_JOB", None) is not None
    if running_as_cron_job:
        dictConfig(make_log_config(log_to_disk=False))
        echo = logger.info  # type: ignore
        api_key = get_cleaner_api_key()
        os.environ[UserSettingsVar.SEMATIC_API_KEY.value] = api_key
        echo("Starting cron cleaner from cron job")
    else:
        echo = click.echo  # type: ignore
        echo("Starting cleaner")

    cleaned_messages = []
    if orphaned_jobs:
        echo("Cleaning orphaned jobs...")
        n_cleaned = clean_orphaned_jobs()
        cleaned_messages.append(f"Cleaned {n_cleaned} orphaned jobs")

    if orphaned_resources:
        echo("Cleaning orphaned resources...")
        n_cleaned = clean_orphaned_resources()
        cleaned_messages.append(f"Cleaned {n_cleaned} orphaned resources")

    if len(cleaned_messages) == 0:
        echo("❌ Nothing to clean.")
    else:
        for message in cleaned_messages:
            echo(f"🧹 {message}")

    echo("Ending cleaner")


def clean_orphaned_jobs() -> int:
    # TODO
    return 0


def clean_orphaned_resources() -> int:
    # TODO
    return 0
