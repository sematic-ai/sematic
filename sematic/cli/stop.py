# Standard Library
import os
import signal

# Third-party
import click

# Sematic
from sematic.cli.cli import cli
from sematic.cli.process_utils import get_server_pid, server_is_running


@cli.command("stop", short_help="Stop the Sematic server")
def stop():
    if not server_is_running():
        click.echo("Sematic is not running.")
        return

    server_pid = get_server_pid()
    # Ideally SIGTERM but I think websocker workers take a while to finish
    os.kill(server_pid, signal.SIGQUIT)
    click.echo("Sematic stopped.")
