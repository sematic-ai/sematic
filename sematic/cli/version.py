# Standard Library
import platform

# Third-party
import click

# Sematic
from sematic.cli.cli import cli
from sematic.versions import CURRENT_VERSION_STR, MIN_CLIENT_SERVER_SUPPORTS_STR


@cli.command("version", short_help="Print version information.")
def version():
    """
    Print the Server, Client, and Python versions.
    """
    click.echo(f"Sematic server v{CURRENT_VERSION_STR} is installed.")
    click.echo(f"Client versions >= v{MIN_CLIENT_SERVER_SUPPORTS_STR} are supported.")
    click.echo(f"Python v{platform.python_version()} is running this binary.")
