# Third-party
import click

# Sematic
import sematic.api_client as api_client
from sematic.cli.cli import cli


@cli.command("cancel", short_help="Cancel a run")
@click.argument("run_id", type=click.STRING)
def cancel(run_id: str):
    """
    Cancel a pipeline execution.
    """
    try:
        run = api_client.get_run(run_id)
    except api_client.BadRequestError:
        click.echo(f"Could not find run {run_id}")
        return

    click.confirm(
        (
            f"Canceling resolution for run {run_id}, "
            "all runs in the pipeline will be cancelled. Proceed?"
        ),
        abort=True,
    )

    api_client.cancel_resolution(run.root_id)

    click.echo("Resolution was canceled succesfully.")
