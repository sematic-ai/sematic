# Standard Library
import sys
from typing import Type

# Third-party
import click

# Sematic
from sematic.abstract_plugin import AbstractPlugin
from sematic.cli.cli import cli
from sematic.config.server_settings import ServerSettings
from sematic.config.settings import (
    delete_plugin_setting,
    dump_settings,
    get_active_settings,
    set_plugin_setting,
)
from sematic.config.user_settings import UserSettings


@cli.group("settings")
def settings() -> None:
    pass


@settings.command("show", short_help="Show the currently active settings")
def show_settings_cli() -> None:
    """
    Show the currently active profile settings.
    """
    settings_dump = dump_settings(get_active_settings())
    click.echo(f"Active profile settings:\n\n{settings_dump}")


@settings.command("set", short_help="Set a user settings value")
@click.argument("var", type=click.STRING)
@click.argument("value", type=click.STRING)
def set_settings_cli(var: str, value: str) -> None:
    """
    Set a setting value.
    """
    _set_plugin_settings_cli(var, value, UserSettings)


def _set_plugin_settings_cli(
    var: str, value: str, plugin: Type[AbstractPlugin]
) -> None:
    settings_vars = plugin.get_settings_vars()

    try:
        settings_var = settings_vars[var]

    except KeyError:
        keys = "\n".join([var.value for var in settings_vars])
        click.echo(
            f"Invalid settings key for {plugin.get_path()}: "
            f"{var}! Available keys:\n{keys}\n"
        )
        sys.exit(1)

    set_plugin_setting(plugin, settings_var, value)
    click.echo(f"Successfully set {var} to {repr(value)}\n")


@settings.command("delete", short_help="Delete a user setting value")
@click.argument("var", type=click.STRING)
def delete_settings_cli(var: str) -> None:
    """
    Delete a user setting value.
    """
    _delete_plugin_settings_cli(var, UserSettings)


def _delete_plugin_settings_cli(var: str, plugin: Type[AbstractPlugin]) -> None:
    settings_vars = plugin.get_settings_vars()

    try:
        settings_var = settings_vars[var]
    except KeyError:
        keys = "\n".join([var.value for var in settings_vars])
        click.echo(f"Invalid user setting key: {var}! Available keys:\n{keys}\n")
        sys.exit(1)

    try:
        delete_plugin_setting(plugin, settings_var)
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
    show_settings_cli()


@server_settings.command("set", short_help="Set a server setting value")
@click.argument("var", type=click.STRING)
@click.argument("value", type=click.STRING)
def set_server_settings_cli(var: str, value: str) -> None:
    """
    Set a server setting value.
    """
    _set_plugin_settings_cli(var=var, value=value, plugin=ServerSettings)


@server_settings.command("delete", short_help="Delete a server setting value")
@click.argument("var", type=click.STRING)
def delete_server_settings_cli(var: str) -> None:
    """
    Delete a server setting value.
    """
    _delete_plugin_settings_cli(var=var, plugin=ServerSettings)
