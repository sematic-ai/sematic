# Standard Library
import logging
import os
from collections import Counter
from logging.config import dictConfig
from typing import List

# Third-party
import click

# Sematic
import sematic.api_client as api_client
from sematic.api.endpoints.auth import get_cleaner_api_key
from sematic.cli.cli import cli
from sematic.config.config import switch_env
from sematic.config.user_settings import UserSettingsVar
from sematic.logging import make_log_config

logger = logging.getLogger(__name__)


@cli.command("clean", short_help="Clean up orphaned objects")
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
@click.option(
    "--force",
    is_flag=True,
    show_default=True,
    default=False,
    help=(
        "Mark the metadata for cleaned objects as being terminal "
        "even if the underlying objects can't be verified as cleaned."
    ),
)
def clean(orphaned_jobs: bool, orphaned_resources: bool, force: bool):
    """
    Clean up objects that are no longer needed.
    """
    running_as_cron_job = os.environ.get("RUNNING_AS_CRON_JOB", None) is not None
    switch_env("user")
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
        messages = clean_orphaned_jobs(force)
        cleaned_messages.extend(messages)

    if orphaned_resources:
        echo("Cleaning orphaned resources...")
        messages = clean_orphaned_resources(force)
        cleaned_messages.extend(messages)

    if len(cleaned_messages) == 0:
        echo("✅ Nothing to clean.")
    else:
        for message in cleaned_messages:
            echo(f"🧹 {message}")

    echo("Ending cleaner")


def clean_orphaned_jobs(force: bool) -> List[str]:
    resolution_ids: List[str] = api_client.get_resolutions_with_orphaned_jobs()
    resolution_updates_by_kind: Counter = Counter()
    for root_id in resolution_ids:
        try:
            logger.info("Cleaning jobs for resolution %s", root_id)
            state_changes = api_client.clean_orphaned_jobs_for_resolution(
                root_id, force
            )
            resolution_updates_by_kind.update(state_changes)
        except Exception:
            logger.exception("Error cleaning jobs for resolution %s", root_id)

    run_ids = api_client.get_runs_with_orphaned_jobs()
    run_updates_by_kind: Counter = Counter()
    for run_id in run_ids:
        try:
            logger.info("Cleaning jobs for run %s", run_id)
            state_changes = api_client.clean_jobs_for_run(run_id, force)
            run_updates_by_kind.update(state_changes)
        except Exception:
            logger.exception("Error cleaning jobs for run %s", run_id)

    messages = ["Resolution jobs:"]
    for change_type, count in resolution_updates_by_kind.items():
        messages.append(f"\t{change_type}: {count}")
    messages.append("Run jobs:")
    for change_type, count in run_updates_by_kind.items():
        messages.append(f"\t{change_type}: {count}")
    return messages


def clean_orphaned_resources(force: bool) -> List[str]:
    resource_ids = api_client.get_orphaned_resource_ids()
    changes_by_kind: Counter = Counter()
    for resource_id in resource_ids:
        try:
            logger.info("Cleaning resource %s", resource_id)
            change_kind = api_client.clean_resource(resource_id, force)
            changes_by_kind.update([change_kind])
        except Exception:
            logger.exception("Error cleaning resource %s", resource_id)
    messages = ["Resources:"]
    for change_type, count in changes_by_kind.items():
        messages.append(f"\t{change_type}: {count}")
    return messages
