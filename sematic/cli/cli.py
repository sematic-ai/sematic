# Third-party
import click


@click.group("sematic")
def cli():
    """
    Welcome to Sematic

    Start Sematic:
        $ sematic start

    Run an example:
        $ sematic run examples/mnist/pytorch
    """
    pass


@cli.group("advanced")
def advanced():
    """
    Advanced operations with the CLI that are primarily useful for
    infrastructure engineers and/or those with deep knowledge of
    Sematic.
    """
    pass
