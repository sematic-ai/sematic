# Third-party
import yaml
import click

# Sematic
from sematic.cli.cli import cli
from sematic.user_settings import SettingsVar, get_all_user_settings, set_user_settings


@cli.group("settings")
def settings():
    pass


@settings.command("show", short_help="Show active settings")
def show_settings():
    """
    Show currently active settings.
    """
    settings = get_all_user_settings()
    click.echo("Active settings:\n")
    click.echo(yaml.dump(settings, default_flow_style=False))


@settings.command("set", short_help="Set settings value")
@click.argument("var", type=click.STRING)
@click.argument("value", type=click.STRING)
def set_settings_cli(var, value):
    """
    Set a settings value
    """
    try:
        settings_var = SettingsVar[var]
        set_user_settings(settings_var, value)
        click.echo("Successfully set {} to {}".format(var, repr(value)))
    except KeyError:
        click.echo(
            "Invalid settings key: {}\n\nAvailable keys are:\n{}".format(
                var, "\n".join([m.value for m in SettingsVar.__members__.values()])
            )
        )
