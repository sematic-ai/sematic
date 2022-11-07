# Standard Library
import sys

# Third-party
import click

# Sematic
from sematic.cli.cli import cli
from sematic.user_settings import (
    SettingsVar,
    delete_profile,
    delete_user_settings,
    dump_profile_settings,
    get_active_user_settings,
    get_profiles,
    set_active_profile,
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
    active_profile, inactive_profiles = get_profiles()
    click.echo(f"Active profile: '{active_profile}'")
    if len(inactive_profiles) > 0:
        click.echo(f"Inactive profiles: {inactive_profiles}")

    profile_settings_dump = dump_profile_settings(get_active_user_settings())
    click.echo(f"\nActive settings:\n{profile_settings_dump}")


@settings.command("set", short_help="Set a setting value for the active profile")
@click.argument("var", type=click.STRING)
@click.argument("value", type=click.STRING)
def set_settings(var: str, value: str) -> None:
    """
    Set a setting value for the active profile.
    """
    try:
        settings_var = SettingsVar[var]
    except KeyError:
        keys = "\n".join([var.value for var in SettingsVar])  # type: ignore
        click.echo(f"Invalid settings key: {var}! Available keys:\n{keys}\n")
        sys.exit(1)

    set_user_settings(settings_var, value)
    click.echo(f"Successfully set {var} to {repr(value)}\n")


@settings.command(
    "delete", short_help="Deletes a setting value from the active profile"
)
@click.argument("var", type=click.STRING)
def delete_settings(var: str) -> None:
    """
    Deletes a setting value from the active profile.
    """
    try:
        settings_var = SettingsVar[var]
    except KeyError:
        keys = "\n".join([var.value for var in SettingsVar])  # type: ignore
        click.echo(f"Invalid settings key: {var}! Available keys:\n{keys}\n")
        sys.exit(1)

    try:
        delete_user_settings(settings_var)
    except ValueError as e:
        click.echo(f"{e}\n")
        sys.exit(1)

    click.echo(f"Successfully deleted {var}\n")


@settings.command("switch-profile", short_help="Sets the currently active profile")
@click.argument("profile", type=click.STRING)
def switch_profile(profile: str) -> None:
    """
    Sets the currently active profile.
    """
    if profile == get_profiles()[0]:
        click.echo(f"The active profile is already set to '{profile}'\n")
        return

    try:
        set_active_profile(profile)
    except ValueError as e:
        click.echo(f"{e}\n")
        sys.exit(1)

    click.echo(f"Successfully set '{profile}' as the active profile\n")

    profile_settings_dump = dump_profile_settings(get_active_user_settings())
    click.echo(f"Active settings:\n{profile_settings_dump}")


@settings.command("delete-profile", short_help="Deletes the specified profile")
@click.argument("profile", type=click.STRING)
def delete_profile_cli(profile: str) -> None:
    """
    Deletes the specified profile.
    """
    try:
        delete_profile(profile)
    except ValueError as e:
        click.echo(f"{e}\n")
        sys.exit(1)

    click.echo(f"Successfully deleted profile '{profile}'\n")
