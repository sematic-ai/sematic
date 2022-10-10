# Third-party
import click

# Sematic
from sematic.cli.cli import cli
import sematic.api_client as api_client


@cli.command("cancel", short_help="Cancel a run")
@click.argument("run_id", type=click.STRING)
def cancel(run_id: str):
    try:
        run = api_client.get_run(run_id)
        root_run = api_client.get_run(run.root_id)
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

    api_client.notify_pipeline_update(root_run.calculator_path)

    click.echo("Resolution was canceled succesfully.")
