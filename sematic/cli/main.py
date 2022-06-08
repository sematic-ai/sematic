# Standard library
import subprocess

# Third-party
import click

# Sematic
from sematic.config import current_env, get_config, switch_env
from sematic.cli.process_utils import (
    server_is_running,
    write_server_pid,
    get_server_pid,
)


@click.group("sematic")
def main():
    """
    Welcome to Sematic
    """
    switch_env("local_sqlite")


@main.command("start", short_help="Start the Sematic app")
def start():
    if server_is_running():
        # The server url may be incorrect here if started with a different env
        # We can save the URL in server.pid, but we can't use the `ps` recovery strategy
        # in `_get_server_pid` if the pid is incorrect
        click.echo("Sematic already running at {}".format(get_config().server_url))
        return

    click.echo("Starting Sematic...")
    process = subprocess.Popen(
        ["python3", "-m", "sematic.api.server", "--env", current_env()]
    )

    write_server_pid(process.pid)

    click.echo("Started with PID {}".format(process.pid))
    click.echo("Visit Sematic at {}".format(get_config().server_url))


@main.command("stop", short_help="Stop the Sematic server")
def stop():
    server_pid = get_server_pid()
    if server_pid is None:
        click.echo("Sematic is not running.")
        return

    process = subprocess.run(
        "kill {}".format(server_pid), shell=True, capture_output=True
    )
    error = process.stderr.decode()

    if process.returncode == 0:
        click.echo("Successfully stopped Sematic.")
    elif "No such process" in error:
        click.echo("Sematic is not running.")
    else:
        click.echo("There was a problem stopping Sematic: {}".format(error))


if __name__ == "__main__":
    main()
