# Standard Library
import logging

# Third-party
import click

# Sematic
from sematic.config.config import switch_env
from sematic.db.migrate import migrate_up


@click.group("sematic")
@click.option("-v", "--verbose", count=True)
def cli(verbose: int):
    """
    Welcome to Sematic

    Start Sematic:
        $ sematic start

    Run an example:
        $ sematic run examples/mnist/pytorch
    """
    if verbose == 1:
        logging.basicConfig(level=logging.INFO)
    elif verbose > 1:
        logging.basicConfig(level=logging.DEBUG)

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
