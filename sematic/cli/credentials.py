# Third-party
import yaml
import click

# Sematic
from sematic.cli.cli import cli
from sematic.credentials import get_credentials, set_credential, CredentialKeys


@cli.group("credentials")
def credentials():
    pass


@credentials.command("show", short_help="Show active credentials")
def show_credentials():
    """
    Show currently active credentials.
    """
    credentials = get_credentials()
    click.echo("Active credentials:\n")
    click.echo(yaml.dump(credentials, default_flow_style=False))


@credentials.command("set", short_help="Set credential value")
@click.argument("app", type=click.STRING)
@click.argument("var", type=click.STRING)
@click.argument("value", type=click.STRING)
def set_credential_cli(app, var, value):
    """
    Set a credential value
    """
    try:
        key = CredentialKeys[app]
    except KeyError:
        click.echo("Unknown app: {}".format(repr(app)))
        click.echo("Available app: {}".format(tuple(CredentialKeys.__members__.keys())))
        return

    set_credential(key, var, value)
    click.echo("Successfully set {} to {}".format(var, repr(value)))
