# Standard library
import os
import importlib

# Third-party
import click

# Sematic
from sematic.config import get_config
from sematic.cli.cli import cli
from sematic.cli.process_utils import server_is_running


def _is_example(script_path: str):
    if not script_path.startswith("examples"):
        return False
    if script_path.endswith(".py"):
        return False

    return os.path.exists(
        os.path.join(
            get_config().base_dir,
            script_path,
            "{}.py".format(get_config().examples_entry_point),
        )
    )


def _example_path_to_import_path(script_path: str) -> str:
    return "sematic.{}".format(script_path.replace("/", "."))


def _get_requirements_path(example_path: str) -> str:
    return os.path.join(
        get_config().base_dir,
        example_path,
        "requirements.txt",
    )


def _get_requirements(example_path: str) -> list[str]:
    with open(_get_requirements_path(example_path), "r") as file:
        return file.read().split("\n")


def _run_example(example_path: str):
    click.echo("Running example {}\n".format(example_path))
    try:
        example_main = importlib.import_module(
            "{}.{}".format(
                _example_path_to_import_path(example_path),
                get_config().examples_entry_point,
            )
        )
        example_main.main()
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


@cli.command("run", short_help="Run a pipeline, or a packaged example")
@click.argument("script_path", type=click.STRING)
def run(script_path: str):
    if not server_is_running():
        click.echo("Sematic is not started, issue `sematic start` first.")
        return

    if _is_example(script_path):
        _run_example(script_path)
