# Standard Library
import platform

# Third-party
import click

# Sematic
from sematic.cli.cli import cli
from sematic import api_client
from sematic.versions import CURRENT_VERSION_STR, version_as_string


@cli.command("version", short_help="Print version information.")
def version():
    """
    Print the Server, Client, and Python versions.
    """
    click.echo(f"Sematic client v{CURRENT_VERSION_STR} is installed.")
    try:
        server_version_metadata = api_client.validate_server_compatibility()
        server_version = version_as_string(server_version_metadata["server"])
        min_client_version = version_as_string(server_version_metadata["min_client_supported"])
        click.echo(f"The server is at version v{server_version}")
        click.echo(f"Client versions >= v{min_client_version} are supported.")
        click.echo(f"Python v{platform.python_version()} is running this binary.")
    except api_client.IncompatibleClientError as e:
        click.echo(str(e))
