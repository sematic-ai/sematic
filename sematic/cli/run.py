# Standard Library
import os
import runpy
import sys
import typing

# Third-party
import click

# Sematic
from sematic.cli.cli import cli
from sematic.cli.examples_utils import is_example
from sematic.cli.process_utils import server_is_running
from sematic.config import get_config


def _example_path_to_import_path(script_path: str) -> str:
    return "sematic.{}".format(script_path.replace("/", "."))


def _get_requirements_path(example_path: str) -> str:
    return os.path.join(
        get_config().base_dir,
        example_path,
        "requirements.txt",
    )


def _get_requirements(example_path: str) -> typing.List[str]:
    with open(_get_requirements_path(example_path), "r") as file:
        return file.read().split("\n")


def _run_example(example_path: str):
    click.echo("Running example {}\n".format(example_path))
    try:
        runpy.run_module(
            _example_path_to_import_path(example_path), run_name="__main__"
        )
        click.echo(
            "\nYou run has completed, view it at {}\n".format(get_config().server_url)
        )
    except ModuleNotFoundError as exception:
        click.echo("{}\n".format(exception))
        click.echo(
            "The following packages are needed to run {}:\n".format(example_path)
        )
        for requirement in _get_requirements(example_path):
            click.echo("\t{}".format(requirement))
        click.echo("To install them run:\n")
        click.echo("\tpip3 install -r {}".format(_get_requirements_path(example_path)))


@cli.command(
    "run",
    short_help="Run a pipeline, or a packaged example",
    context_settings=dict(
        ignore_unknown_options=True,
        allow_extra_args=True,
    ),
)
@click.argument("script_path", type=click.STRING)
@click.pass_context
def run(ctx, script_path: str):
    if not server_is_running():
        click.echo("Sematic is not started, issue `sematic start` first.")
        return

    if is_example(script_path):
        _run_example(script_path)
        return

    # This is ugly, better way to do this?
    sys.argv = [sys.argv[0]] + ctx.args

    runpy.run_module(script_path, run_name="__main__")
