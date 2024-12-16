# Standard Library
import logging
import os
from collections import Counter
from typing import Callable, List

# Third-party
import click

# Sematic
import sematic.api_client as api_client
from sematic.api.endpoints.auth import get_cleaner_api_key
from sematic.cli.cli import cli
from sematic.config.config import switch_env
from sematic.config.user_settings import UserSettingsVar


logger = logging.getLogger(__name__)


@cli.command("clean", short_help="Clean up orphaned objects")  # type: ignore
@click.option(
    "--orphaned-runs",
    is_flag=True,
    show_default=True,
    default=False,
    help="Clean runs whose associated pipeline runs have stopped.",
)
@click.option(
    "--stale-pipeline-runs",
    is_flag=True,
    show_default=True,
    default=False,
    help="Clean pipeline runs whose root runs have stopped.",
)
@click.option(
    "--zombie-pipeline-runs",
    is_flag=True,
    show_default=True,
    default=False,
    help="Clean pipeline runs whose kubernetes pods are gone.",
)
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
def clean(
    orphaned_runs: bool,
    stale_pipeline_runs: bool,
    zombie_pipeline_runs: bool,
    orphaned_jobs: bool,
    orphaned_resources: bool,
    force: bool,
):
    """
    Clean up objects that are no longer needed.
    """
    switch_env("user")
    running_as_cron_job = os.environ.get("RUNNING_AS_CLEANER_CRON_JOB", None) is not None
    if running_as_cron_job:
        echo = logger.info  # type: ignore
        api_key = get_cleaner_api_key()
        os.environ[UserSettingsVar.SEMATIC_API_KEY.value] = api_key
        echo("Starting cron cleaner from cron job")
    else:
        echo = click.echo  # type: ignore
        echo("Starting cleaner")

    cleaned_messages = []
    if orphaned_runs:
        echo("Cleaning orphaned runs...")
        messages = clean_orphaned_runs()
        cleaned_messages.extend(messages)

    if zombie_pipeline_runs:
        echo("Cleaning zombie pipeline runs...")
        messages = clean_zombie_pipeline_runs()
        cleaned_messages.extend(messages)

    if stale_pipeline_runs:
        echo("Cleaning stale pipeline runs...")
        messages = clean_stale_pipeline_runs()
        cleaned_messages.extend(messages)

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


def clean_orphaned_runs() -> List[str]:
    return clean_ids(
        ids=api_client.get_orphaned_run_ids(),
        object_name="run",
        clean_query=api_client.clean_orphaned_run,
    )


def clean_stale_pipeline_runs() -> List[str]:
    return clean_ids(
        ids=api_client.get_pipeline_runs_with_stale_statuses(),
        object_name="pipeline_run",
        clean_query=api_client.clean_pipeline_run,
    )


def clean_zombie_pipeline_runs() -> List[str]:
    return clean_ids(
        ids=api_client.get_zombie_pipeline_run_ids(),
        object_name="pipeline_run",
        clean_query=api_client.clean_pipeline_run,
    )


def clean_ids(
    ids: List[str], object_name: str, clean_query: Callable[[str], str]
) -> List[str]:
    updates_by_kind: Counter = Counter()
    for id_ in ids:
        try:
            logger.info("Cleaning %s %s", object_name, id_)
            state_change = clean_query(id_)
            updates_by_kind.update([state_change])
        except Exception:
            logger.exception("Error cleaning up %s %s", object_name, id_)

    return messages_from_counter(f"{object_name.capitalize()}s:", updates_by_kind)


def clean_orphaned_jobs(force: bool) -> List[str]:
    pipeline_run_ids: List[str] = api_client.get_pipeline_run_ids_with_orphaned_jobs()
    pipeline_run_updates_by_kind: Counter = Counter()
    for root_id in pipeline_run_ids:
        try:
            logger.info("Cleaning jobs for pipeline_run %s", root_id)
            state_changes = api_client.clean_orphaned_jobs_for_pipeline_run(
                root_id, force
            )
            pipeline_run_updates_by_kind.update(state_changes)
        except Exception:
            logger.exception("Error cleaning jobs for pipeline_run %s", root_id)

    run_ids = api_client.get_run_ids_with_orphaned_jobs()
    run_updates_by_kind: Counter = Counter()
    for run_id in run_ids:
        try:
            logger.info("Cleaning jobs for run %s", run_id)
            state_changes = api_client.clean_jobs_for_run(run_id, force)
            run_updates_by_kind.update(state_changes)
        except Exception:
            logger.exception("Error cleaning jobs for run %s", run_id)

    messages = messages_from_counter("Runner jobs:", pipeline_run_updates_by_kind)
    messages.extend(messages_from_counter("Function jobs:", run_updates_by_kind))
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
    messages = messages_from_counter("Resources:", changes_by_kind)
    return messages


def messages_from_counter(header_line: str, counter: Counter) -> List[str]:
    messages = [header_line]
    for change_type, count in counter.items():
        messages.append(f"\t{change_type}: {count}")
    return messages
