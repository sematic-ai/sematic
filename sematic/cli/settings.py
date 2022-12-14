# Standard Library
import sys

# Third-party
import click

# Sematic
from sematic.cli.cli import cli
from sematic.config.server_settings import (
    ServerSettingsVar,
    delete_server_settings,
    get_active_server_settings,
    set_server_settings,
)
from sematic.config.settings import dump_settings
from sematic.config.user_settings import (
    UserSettingsVar,
    delete_user_settings,
    get_active_user_settings,
    set_user_settings,
)


@cli.group("settings")
def settings() -> None:
    pass


@settings.command("show", short_help="Show the currently active user settings")
def show_user_settings_cli() -> None:
    """
    Show the currently active user settings.
    """
    settings_dump = dump_settings(get_active_user_settings())
    click.echo(f"Active user settings:\n\n{settings_dump}")


@settings.command("set", short_help="Set a user settings value")
@click.argument("var", type=click.STRING)
@click.argument("value", type=click.STRING)
def set_user_settings_cli(var: str, value: str) -> None:
    """
    Set a user settings value.
    """
    try:
        settings_var = UserSettingsVar[var]

    except KeyError:
        keys = "\n".join([var.value for var in UserSettingsVar])  # type: ignore
        click.echo(f"Invalid user settings key: {var}! Available keys:\n{keys}\n")
        sys.exit(1)

    set_user_settings(settings_var, value)
    click.echo(f"Successfully set {var} to {repr(value)}\n")


@settings.command("delete", short_help="Delete a user settings value")
@click.argument("var", type=click.STRING)
def delete_user_settings_cli(var: str) -> None:
    """
    Delete a user settings value.
    """
    try:
        settings_var = UserSettingsVar[var]
    except KeyError:
        keys = "\n".join([var.value for var in UserSettingsVar])  # type: ignore
        click.echo(f"Invalid user settings key: {var}! Available keys:\n{keys}\n")
        sys.exit(1)

    try:
        delete_user_settings(settings_var)
    except ValueError as e:
        click.echo(f"{e}\n")
        sys.exit(1)

    click.echo(f"Successfully deleted {var}\n")


@cli.group("server-settings")
def server_settings() -> None:
    pass


@server_settings.command("show", short_help="Show the currently active server settings")
def show_server_settings_cli() -> None:
    """
    Show the currently active server settings.
    """
    settings_dump = dump_settings(get_active_server_settings())
    click.echo(f"Active server settings:\n\n{settings_dump}")


@server_settings.command("set", short_help="Set a server settings value")
@click.argument("var", type=click.STRING)
@click.argument("value", type=click.STRING)
def set_server_settings_cli(var: str, value: str) -> None:
    """
    Set a server settings value.
    """
    try:
        settings_var = ServerSettingsVar[var]

    except KeyError:
        keys = "\n".join([var.value for var in ServerSettingsVar])  # type: ignore
        click.echo(f"Invalid server settings key: {var}! Available keys:\n{keys}\n")
        sys.exit(1)

    set_server_settings(settings_var, value)
    click.echo(f"Successfully set {var} to {repr(value)}\n")


@server_settings.command("delete", short_help="Delete a server settings value")
@click.argument("var", type=click.STRING)
def delete_server_settings_cli(var: str) -> None:
    """
    Delete a server settings value.
    """
    try:
        settings_var = ServerSettingsVar[var]
    except KeyError:
        keys = "\n".join([var.value for var in ServerSettingsVar])  # type: ignore
        click.echo(f"Invalid server settings key: {var}! Available keys:\n{keys}\n")
        sys.exit(1)

    try:
        delete_server_settings(settings_var)
    except ValueError as e:
        click.echo(f"{e}\n")
        sys.exit(1)

    click.echo(f"Successfully deleted {var}\n")
