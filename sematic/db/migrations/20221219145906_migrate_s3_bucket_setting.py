# Standard Library
import os
import pathlib

# Third-party
import yaml

_S3_PLUGIN_PATH = "sematic.plugins.storage.s3_storage.S3Storage"
_SERVER_SETTINGS_PATH = "sematic.config.server_settings.ServerSettings"
_AWS_S3_BUCKET_SETTING_KEY = "AWS_S3_BUCKET"


def up():
    """
    Copies the AWS_S3_BUCKET setting from ServerSettings to S3Storage plugin settings.
    """
    settings_file_path = _get_settings_file_path()

    if not os.path.isfile(settings_file_path):
        return

    with open(settings_file_path, "r") as f:
        settings = yaml.load(f, Loader=yaml.Loader)

    if settings is None:
        return

    s3_bucket_setting = (
        settings.get("default", {})
        .get("settings", {})
        .get(_SERVER_SETTINGS_PATH, {})
        .get(_AWS_S3_BUCKET_SETTING_KEY)
    )

    if s3_bucket_setting is None:
        return

    if _S3_PLUGIN_PATH not in settings["default"]["settings"]:
        settings["default"]["settings"][_S3_PLUGIN_PATH] = {}

    settings["default"]["settings"][_S3_PLUGIN_PATH][
        _AWS_S3_BUCKET_SETTING_KEY
    ] = s3_bucket_setting

    with open(settings_file_path, "w") as f:
        f.write(yaml.dump(settings, Dumper=yaml.Dumper))


def down():
    """
    Removes S3Storage plugin settings.
    """

    settings_file_path = _get_settings_file_path()

    if not os.path.isfile(settings_file_path):
        return

    with open(settings_file_path, "r") as f:
        settings = yaml.load(f, Loader=yaml.Loader)

    if _S3_PLUGIN_PATH in settings.get("profiles", {}).get("settings", {}):
        del settings["profiles"]["settings"][_S3_PLUGIN_PATH]

    with open(settings_file_path, "w") as f:
        f.write(yaml.dump(settings, Dumper=yaml.Dumper))


def _get_settings_file_path() -> str:
    config_dir_path = _get_config_dir()
    return os.path.join(config_dir_path, "settings.yaml")


def _get_config_dir() -> pathlib.Path:
    config_dir = os.environ.get("SEMATIC_CONFIG_DIR", ".sematic")
    config_dir_path = pathlib.Path(config_dir)

    if not config_dir_path.is_absolute():
        home_dir = pathlib.Path.home()
        config_dir_path = home_dir / config_dir_path

    return config_dir_path
