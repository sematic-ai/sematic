# Standard library
import os
import shutil
from typing import Optional

# Third-party
import click

# Sematic
from sematic.cli.cli import cli
from sematic.cli.examples_utils import all_examples, is_example
from sematic.config import get_config


@cli.command("new", short_help="Create new project")
@click.argument("project_name", type=click.STRING)
@click.option(
    "--from",
    "from_example",
    type=click.STRING,
    help="Create a new project from an example template",
)
def new(project_name: str, from_example: Optional[str]):
    """
    Create a new project with a scaffold or from an existing example.
    """
    source_path = get_config().project_template_dir
    from_suffix = ""

    if from_example is not None:
        if not is_example(from_example):
            click.echo("No such example: {}\n".format(from_example))
            click.echo("Available examples are:")

            for example in all_examples():
                click.echo("\t{}".format(example))

            return

        source_path = os.path.join(get_config().base_dir, from_example)
        from_suffix = " from {}".format(from_example)

    project_path = os.path.join(os.getcwd(), project_name)

    if os.path.isdir(project_path):
        click.echo("{} already exists.".format(project_path))
        return

    shutil.copytree(source_path, project_path)

    click.echo("New project scaffold created at {}{}".format(project_path, from_suffix))
