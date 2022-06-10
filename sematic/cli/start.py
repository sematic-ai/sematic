# Standard library
import os
import webbrowser

# Third-party
import click

# Sematic
from sematic.config import get_config
from sematic.cli.process_utils import (
    server_is_running,
)
from sematic.api.server import run_wsgi
from sematic.cli.cli import cli


@cli.command("start", short_help="Start the Sematic app")
def start():
    if server_is_running():
        click.echo("Sematic is already running.")
        return

    click.echo("Starting Sematic...")
    click.echo("Visit Sematic at {}".format(get_config().server_url))

    if os.fork():
        webbrowser.open(get_config().server_url, new=0, autoraise=True)

        os._exit(0)

    run_wsgi(False)
