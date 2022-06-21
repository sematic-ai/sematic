# Standard library
import os
import re
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
    if from_example is None:
        from_example = "examples/template"

    if not is_example(from_example):
        click.echo("No such example: {}\n".format(from_example))
        click.echo("Available examples are:")

        for example in all_examples():
            click.echo("\t{}".format(example))

        return

    source_path = os.path.join(get_config().base_dir, from_example)
    from_suffix = " from {}".format(from_example)
    example_module = ".".join(from_example.split("/"))

    project_path = os.path.join(os.getcwd(), project_name)

    if os.path.isdir(project_path):
        click.echo("{} already exists.".format(project_path))
        return

    shutil.copytree(source_path, project_path)

    for dir, _, files in os.walk(project_name):
        for filename in files:
            if not filename.endswith(".py"):
                continue

            with open(os.path.join(dir, filename), "r+") as file:
                content = file.read()
                file.seek(0)
                content = re.sub(
                    r"from sematic.{}".format(example_module),
                    "from {}".format(project_name),
                    content,
                )
                file.write(content)
                file.truncate()

    click.echo("New project scaffold created at {}{}".format(project_path, from_suffix))
