# Standard Library
import math
import os
import runpy
import sys
import time
from logging.config import dictConfig
from typing import List, Tuple

# Third-party
import click

# Sematic
from sematic.api_client import validate_server_compatibility
from sematic.cli.cli import cli
from sematic.cli.examples_utils import is_example
from sematic.config.config import get_config, switch_env
from sematic.logs import make_log_config
from sematic.plugins.abstract_builder import get_builder_plugin
from sematic.plugins.building.docker_builder import DockerBuilder


def _example_path_to_import_path(script_path: str) -> str:
    return "sematic.{}".format(script_path.replace("/", "."))


def _get_requirements_path(example_path: str) -> str:
    return os.path.join(
        get_config().base_dir,
        example_path,
        "requirements.txt",
    )


def _get_requirements(example_path: str) -> List[str]:
    with open(_get_requirements_path(example_path), "r") as file:
        return file.read().split("\n")


def _run_example(example_path: str):
    try:
        runpy.run_module(_example_path_to_import_path(example_path), run_name="__main__")
        click.echo(
            "\nYou run has completed, view it at {}\n".format(get_config().server_url)
        )
    except ModuleNotFoundError as exception:
        click.echo("{}\n".format(exception))
        click.echo("The following packages are needed to run {}:\n".format(example_path))
        for requirement in _get_requirements(example_path):
            click.echo("\t{}".format(requirement))
        click.echo("To install them run:\n")
        click.echo("\tpip3 install -r {}".format(_get_requirements_path(example_path)))


@cli.command("run", short_help="Run a pipeline, or a packaged example.")  # type: ignore
@click.option(
    "-b",
    "--build",
    help=(
        "Build a container image that will be used to execute the pipeline, "
        "using the configured build plugin. Defaults to `False`. "
        "If not set, the pipeline will be run locally in the current environment."
    ),
    default=False,
    is_flag=True,
)
@click.option(
    "-n",
    "--no-cache",
    help=(
        "When `--build` is specified, builds the image from scratch, "
        "ignoring previous versions. Defaults to `False`."
    ),
    default=False,
    is_flag=True,
)
@click.option(
    "-l",
    "--log-level",
    help=(
        "The log level to use for building and launching the pipeline. "
        "Defaults to `INFO`."
    ),
    default="INFO",
)
@click.argument("script_path", type=click.STRING)
@click.argument("script_arguments", nargs=-1, type=click.STRING)
def run(
    build: bool,
    no_cache: bool,
    log_level: str,
    script_path: str,
    script_arguments: Tuple[str],
):
    # custom option validation
    if no_cache and not build:
        click.echo("Can only pass `--no-cache` together with `--build`.")
        sys.exit(1)

    # ensure the client is pointing to the intended server
    switch_env("user")
    dictConfig(make_log_config(log_to_disk=False, level=log_level))

    # ensure the server is reachable before doing all the work
    validate_server_compatibility(use_cached=False)

    run_command = " ".join(sys.argv)
    # This is ugly, better way to do this?
    sys.argv = [script_path] + list(script_arguments)
    pseudo_command = " ".join(sys.argv)

    if is_example(script_path):
        click.echo(f"Running example script: {pseudo_command}")
        _run_example(example_path=script_path)
        return

    if os.path.splitext(script_path)[1] != ".py":
        click.echo(f"Can only run Python files; got: '{script_path}'", err=True)
        sys.exit(1)

    if not build:
        click.echo(f"Running script locally: {pseudo_command}")
        runpy.run_path(path_name=script_path, run_name="__main__")
        return

    builder_class = get_builder_plugin(default=DockerBuilder)
    builder = builder_class(no_cache=no_cache)

    click.echo(f"Building image and launching: {pseudo_command}")
    start_time = time.time()
    builder.build_and_launch(target=script_path, run_command=run_command)
    stop_time = time.time()

    duration_seconds = math.floor((stop_time - start_time) * 100) / 100.0
    click.echo(f"Built and launched '{script_path}' in {duration_seconds}s")
