# Third-party
import click

# Sematic
from sematic.config import switch_env
from sematic.db.migrate import migrate_up


@click.group("sematic")
def cli():
    """
    Welcome to Sematic

    Start Sematic:
        $ sematic start

    Run an example:
        $ sematic run examples/mnist/pytorch
    """
    switch_env("local")
    migrate_up()
