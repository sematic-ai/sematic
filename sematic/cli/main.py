# Standard library
import os
import signal
import webbrowser

# Third-party
import click

# Sematic
from sematic.config import get_config, switch_env
from sematic.cli.process_utils import (
    server_is_running,
    get_server_pid,
)
from sematic.api.server import run_wsgi


@click.group("sematic")
def main():
    """
    Welcome to Sematic
    """
    switch_env("local_sqlite")


@main.command("start", short_help="Start the Sematic app")
def start():
    if server_is_running():
        click.echo("Sematic is already running.")
        return

    click.echo("Starting Sematic...")
    click.echo("Visit Sematic at {}".format(get_config().server_url))

    if os.fork():
        webbrowser.open(get_config().server_url, new=2, autoraise=True)
        os._exit(0)
    run_wsgi(False)


@main.command("stop", short_help="Stop the Sematic server")
def stop():
    if not server_is_running():
        click.echo("Sematic is not running.")
        return

    server_pid = get_server_pid()
    # Ideally SIGTERM but I think websocker workers take a while to finish
    os.kill(server_pid, signal.SIGQUIT)
    click.echo("Sematic stopped.")


if __name__ == "__main__":
    main()
