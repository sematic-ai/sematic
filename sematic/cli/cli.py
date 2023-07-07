# Standard Library
import logging
import os
from logging.config import dictConfig

# Third-party
import click

# Sematic
from sematic.config.config import switch_env
from sematic.db.migrate import migrate_up
from sematic.logs import make_log_config


@click.group("sematic")  # type: ignore
@click.option("-v", "--verbose", count=True)
def cli(verbose: int):
    """
    Welcome to Sematic

    Start Sematic:
        $ sematic start

    Run an example:
        $ sematic run examples/mnist/pytorch
    """
    if "BUILD_WORKING_DIRECTORY" in os.environ:
        # if the CLI is being executed via bazel (ex: during development
        # of the CLI), run from the directory the user invoked bazel
        # from, rather than the sandbox dir bazel uses by default. That
        # emulates how the real CLI will behave more accurately.
        os.chdir(os.environ["BUILD_WORKING_DIRECTORY"])
    if verbose == 1:
        dictConfig(make_log_config(log_to_disk=False, level=logging.INFO))
    elif verbose > 1:
        dictConfig(make_log_config(log_to_disk=False, level=logging.DEBUG))
        pass

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
