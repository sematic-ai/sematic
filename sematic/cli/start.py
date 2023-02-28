"""
Module containing logic for the `start` CLI command.
"""
# Standard Library
import os
import webbrowser

# Third-party
import click

# Sematic
from sematic.api.server import run_socketio
from sematic.cli.cli import cli
from sematic.cli.process_utils import server_is_running
from sematic.config.config import get_config


@cli.command("start", short_help="Start the Sematic app")
def start():
    """
    Start the web app (API + UI).
    """
    if server_is_running():
        click.echo("Sematic is already running.")
        return

    click.echo("Starting Sematic...")
    click.echo("Visit Sematic at {}".format(get_config().server_url))

    if os.fork():
        webbrowser.open(get_config().server_url, new=0, autoraise=True)

        os._exit(0)

    # This enables us to use websockets and standard HTTP
    # requests in the same server locally, which is what
    # we want. If you try to use Gunicorn to do this,
    # gevent will complain about not monkey patching
    # early enough, unless you have the gevent monkey
    # patch applied VERY early (like user/sitecustomize).
    # monkey patching:
    # https://github.com/gevent/gevent/issues/1235
    run_socketio(False)
