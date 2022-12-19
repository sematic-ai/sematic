# Standard Library
import os
import pathlib
from typing import Any, Dict

# Third-party
import yaml

THIS_MIGRATION_SCHEMA_VERSION = 1


def up():
    config_dir_path = _get_config_dir()
    user_settings_file_path = os.path.join(config_dir_path, "settings.yaml")
    server_settings_file_path = os.path.join(config_dir_path, "server.yaml")

    user_loaded_yaml = _load_settings_yaml("settings.yaml")
    server_loaded_yaml = _load_settings_yaml("server.yaml")

    schema_version = user_loaded_yaml.get("version", 0)

    if schema_version != THIS_MIGRATION_SCHEMA_VERSION - 1:
        raise RuntimeError(
            f"Cannot upgrade settings file from version {schema_version} "
            "to version {THIS_MIGRATION_SCHEMA_VERSION}"
        )

    new_settings = {
        "version": THIS_MIGRATION_SCHEMA_VERSION,
        "profiles": {
            "default": {
                "scopes": {},
                "settings": {
                    "sematic.config.user_settings.UserSettings": user_loaded_yaml.get(
                        "default", {}
                    ),
                    "sematic.config.server_settings.ServerSettings": server_loaded_yaml.get(  # noqa: E501
                        "default", {}
                    ),
                },
            }
        },
    }

    with open(user_settings_file_path, "w") as f:
        f.write(yaml.dump(new_settings, Dumper=yaml.Dumper))

    os.remove(server_settings_file_path)


def down():
    loaded_yaml = _load_settings_yaml("settings.yaml")

    if len(loaded_yaml) == 0:
        return

    schema_version = loaded_yaml.get("version", "'unknown'")

    if schema_version != THIS_MIGRATION_SCHEMA_VERSION:
        raise RuntimeError(
            f"Cannot downgrade settings file from version {schema_version} "
            f"to version {THIS_MIGRATION_SCHEMA_VERSION}"
        )

    old_user_settings = {
        "default": loaded_yaml.get("profiles", {})
        .get("default", {})
        .get("settings", {})
        .get("sematic.config.user_settings.UserSettings", {})
    }

    old_server_settings = {
        "default": loaded_yaml.get("profiles", {})
        .get("default", {})
        .get("settings", {})
        .get("sematic.config.server_settings.ServerSettings", {})
    }

    config_dir_path = _get_config_dir()
    user_settings_file_path = os.path.join(config_dir_path, "settings.yaml")
    server_settings_file_path = os.path.join(config_dir_path, "server.yaml")

    with open(user_settings_file_path, "w") as f:
        f.write(yaml.dump(old_user_settings, Dumper=yaml.Dumper))

    with open(server_settings_file_path, "w") as f:
        f.write(yaml.dump(old_server_settings, Dumper=yaml.Dumper))


def _load_settings_yaml(file_name: str) -> Dict[str, Any]:
    config_dir_path = _get_config_dir()
    settings_file_path = os.path.join(config_dir_path, file_name)

    if os.path.isfile(settings_file_path):
        with open(settings_file_path, "r") as f:
            return yaml.load(f, yaml.Loader)

    return {}


def _get_config_dir() -> pathlib.Path:
    config_dir = os.environ.get("SEMATIC_CONFIG_DIR", ".sematic")
    config_dir_path = pathlib.Path(config_dir)

    if not config_dir_path.is_absolute():
        home_dir = pathlib.Path.home()
        config_dir_path = home_dir / config_dir_path

    return config_dir_path
