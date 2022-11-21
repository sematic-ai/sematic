# Standard Library
import os
from typing import Dict, Union

# Third-party
import yaml

# Sematic
from sematic.config.server_settings import _get_server_settings_file
from sematic.config.settings import EnumDumper
from sematic.config.user_settings import _DEFAULT_PROFILE, _get_user_settings_file

_SERVER_SETTINGS = {
    "SEMATIC_AUTHENTICATE",
    "SEMATIC_AUTHORIZED_EMAIL_DOMAIN",
    "SEMATIC_WORKER_API_ADDRESS",
    "GOOGLE_OAUTH_CLIENT_ID",
    "GITHUB_OAUTH_CLIENT_ID",
    "KUBERNETES_NAMESPACE",
    "GRAFANA_PANEL_URL",
    "AWS_S3_BUCKET",
}
_USER_SETTINGS = {
    "SEMATIC_API_ADDRESS",
    "SEMATIC_API_KEY",
    "SNOWFLAKE_USER",
    "SNOWFLAKE_PASSWORD",
    "SNOWFLAKE_ACCOUNT",
}


def _load_settings(file_path: str) -> Dict[str, Union[str, Dict[str, str]]]:
    """
    Loads the settings from the specified settings file, returning their raw string
    representations, or an empty dict if the file is not found.
    """
    try:
        with open(file_path, "r") as f:
            return yaml.load(f, yaml.Loader)

    except FileNotFoundError:
        return {}


def _save_settings(
    file_path: str, settings: Dict[str, Union[str, Dict[str, str]]]
) -> None:
    """
    Persists the specified settings to the specified settings file.
    """
    yaml_output = yaml.dump(settings, Dumper=EnumDumper)

    with open(file_path, "w") as f:
        f.write(yaml_output)


def up():
    """
    Migrates and removes settings which have been removed from the user settings to the
    server settings.
    """
    # check if settings are permanently configured and not just injected via the env
    if not os.path.isfile(_get_user_settings_file()):
        return

    raw_user_settings = _load_settings(_get_user_settings_file())

    # nothing to migrate
    if raw_user_settings is None or _DEFAULT_PROFILE not in raw_user_settings:
        return

    raw_profile_settings = raw_user_settings[_DEFAULT_PROFILE]

    raw_server_settings = _load_settings(_get_server_settings_file())

    # save each server settings value to the server settings file, and remove them
    # from the user settings dict
    for var in _SERVER_SETTINGS:
        if var in raw_profile_settings:
            raw_server_settings[var] = raw_profile_settings[var]
            del raw_profile_settings[var]

    # save just the user settings back to the user settings file
    _save_settings(_get_user_settings_file(), raw_user_settings)
    # and the server settings to the server settings file
    _save_settings(_get_server_settings_file(), raw_server_settings)


def down():
    """
    Migrates server settings back to the user settings.
    """
    # check if settings are permanently configured and not just injected via the env
    if not os.path.isfile(_get_server_settings_file()):
        return

    raw_server_settings = _load_settings(_get_server_settings_file())

    if raw_server_settings is None:
        # delete the server settings file
        os.unlink(_get_server_settings_file())
        return

    raw_user_settings = _load_settings(_get_user_settings_file())

    if raw_user_settings is None or _DEFAULT_PROFILE not in raw_user_settings:
        raw_user_settings = {_DEFAULT_PROFILE: {}}

    raw_profile_settings = raw_user_settings[_DEFAULT_PROFILE]

    # save each server settings value to the server settings file, and remove them
    # from the user settings dict
    for var in _SERVER_SETTINGS:
        if var in raw_server_settings:
            raw_profile_settings[var] = raw_server_settings[var]

    # save everything back to the user settings file
    _save_settings(_get_user_settings_file(), raw_user_settings)
    # delete the server settings file
    os.unlink(_get_server_settings_file())
