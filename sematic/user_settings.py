# Standard Library
import enum
import logging
import os
from typing import Dict, Optional

# Third-arty
import yaml

# Sematic
from sematic.config_dir import get_config_dir

_SETTINGS_FILE = "settings.yaml"


logger = logging.getLogger(__name__)


Settings = Dict[str, Dict[str, str]]


def _settings_file() -> str:
    return os.path.join(get_config_dir(), _SETTINGS_FILE)


def _load_settings():
    try:
        with open(_settings_file(), "r") as f:
            settings = yaml.load(f, yaml.Loader)
    except FileNotFoundError:
        settings = None

    if settings is None:
        settings = {"default": {}}

    return settings


_settings: Optional[Settings] = None


def get_all_user_settings() -> Dict[str, str]:
    """
    Main API to access stored user settings.
    """
    global _settings

    if _settings is None:
        _settings = _load_settings()

        # Override with env vars
        for var in SettingsVar.__members__.values():
            if var.value in os.environ:
                logger.debug(
                    "Override {} with {}".format(var.value, os.environ[var.value])
                )
                _settings["default"][var.value] = os.environ[var.value]

    return _settings["default"]


class SettingsVar(enum.Enum):
    # Sematic
    SEMATIC_API_ADDRESS = "SEMATIC_API_ADDRESS"
    SEMATIC_WORKER_API_ADDRESS = "SEMATIC_WORKER_API_ADDRESS"
    SEMATIC_API_KEY = "SEMATIC_API_KEY"
    SEMATIC_AUTHENTICATE = "SEMATIC_AUTHENTICATE"
    SEMATIC_AUTHORIZED_EMAIL_DOMAIN = "SEMATIC_AUTHORIZED_EMAIL_DOMAIN"

    # Google
    GOOGLE_OAUTH_CLIENT_ID = "GOOGLE_OAUTH_CLIENT_ID"

    # Github
    GITHUB_OAUTH_CLIENT_ID = "GITHUB_OAUTH_CLIENT_ID"

    # Kubernetes
    KUBERNETES_NAMESPACE = "KUBERNETES_NAMESPACE"

    # Snowflake
    SNOWFLAKE_USER = "SNOWFLAKE_USER"
    SNOWFLAKE_PASSWORD = "SNOWFLAKE_PASSWORD"
    SNOWFLAKE_ACCOUNT = "SNOWFLAKE_ACCOUNT"

    # AWS
    AWS_S3_BUCKET = "AWS_S3_BUCKET"

    # GRAFANA
    GRAFANA_PANEL_URL = "GRAFANA_PANEL_URL"


class MissingSettingsError(Exception):
    def __init__(self, missing_settings: SettingsVar):
        message = """
Missing settings: {}

Set it with

    $ sematic settings set {} VALUE
""".format(
            missing_settings.value, missing_settings.value
        )
        super().__init__(message)


def get_user_settings(var: SettingsVar, *args) -> str:
    """
    Main API to access individual settings.

    Default as first args or will raise if no settings.
    """
    if var not in SettingsVar.__members__.values():
        raise ValueError(
            "Invalid settings var: {}. Available vars: {}".format(
                repr(var), SettingsVar.__members__.values()
            )
        )

    settings = get_all_user_settings().get(var.value)

    if settings is None:
        if len(args) >= 1:
            return args[0]

        raise MissingSettingsError(var)

    return settings


def set_user_settings(var: SettingsVar, value: str):
    if var not in SettingsVar.__members__.values():
        raise ValueError(
            "Invalid settings key: {}. Available keys:\n{}".format(
                repr(var),
                "\n".join([m.value for m in SettingsVar.__members__.values()]),
            )
        )

    saved_settings = _load_settings()

    saved_settings["default"][var.value] = value
    yaml_output = yaml.dump(saved_settings, Dumper=yaml.Dumper)

    with open(_settings_file(), "w") as f:
        f.write(yaml_output)
