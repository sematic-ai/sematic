# Third-party
import click

# Sematic
import sematic.api_client as api_client
from sematic.cli.cli import cli
from sematic.config.config import switch_env


@cli.command("cancel", short_help="Cancel a run")  # type: ignore
@click.argument("run_id", type=click.STRING)
def cancel(run_id: str):
    """
    Cancel a pipeline execution.
    """
    switch_env("user")  # we want to always connect to the API in the user's config
    try:
        run = api_client.get_run(run_id)
    except api_client.BadRequestError:
        click.echo(f"Could not find run {run_id}")
        return

    click.confirm(
        (
            f"Canceling pipeline run {run_id}, "
            f"all runs in the pipeline will be cancelled. Proceed?"
        ),
        abort=True,
    )

    api_client.cancel_pipeline_run(run.root_id)

    click.echo("Pipeline run was canceled successfully.")
