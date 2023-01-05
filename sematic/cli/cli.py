# Third-party
import click

# Sematic
from sematic.config.config import switch_env
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


@cli.group("advanced")
def advanced():
    """
    Advanced operations with the CLI that are primarily useful for
    infrastructure engineers and/or those with deep knowledge of
    Sematic.
    """
    pass
