# Standard Library
import sys

# Third-party
import click

# Sematic
from sematic.cli.cli import cli
from sematic.config.user_settings import (
    UserSettingsVar,
    delete_user_settings,
    dump_settings,
    get_active_user_settings,
    set_user_settings,
)


@cli.group("settings")
def settings() -> None:
    pass


@settings.command("show", short_help="Show the currently active settings")
def show_settings() -> None:
    """
    Show the currently active settings.
    """
    profile_settings_dump = dump_settings(get_active_user_settings())
    click.echo(f"Active settings:\n{profile_settings_dump}")


@settings.command("set", short_help="Set a settings value")
@click.argument("var", type=click.STRING)
@click.argument("value", type=click.STRING)
def set_settings(var: str, value: str) -> None:
    """
    Set a settings value.
    """
    try:
        settings_var = UserSettingsVar[var]

    except KeyError:
        keys = "\n".join([var.value for var in UserSettingsVar])  # type: ignore
        click.echo(f"Invalid settings key: {var}! Available keys:\n{keys}\n")
        sys.exit(1)

    set_user_settings(settings_var, value)
    click.echo(f"Successfully set {var} to {repr(value)}\n")


@settings.command("delete", short_help="Delete a settings value")
@click.argument("var", type=click.STRING)
def delete_settings(var: str) -> None:
    """
    Delete a settings value
    """
    try:
        settings_var = UserSettingsVar[var]
    except KeyError:
        keys = "\n".join([var.value for var in UserSettingsVar])  # type: ignore
        click.echo(f"Invalid settings key: {var}! Available keys:\n{keys}\n")
        sys.exit(1)

    try:
        delete_user_settings(settings_var)
    except ValueError as e:
        click.echo(f"{e}\n")
        sys.exit(1)

    click.echo(f"Successfully deleted {var}\n")
