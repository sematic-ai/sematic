# Standard Library
import os
import shutil

# Third-party
import yaml

# Sematic
from sematic.config.config_dir import get_config_dir
from sematic.config.settings import EnumDumper, get_settings


def up():
    server_settings_file_path = os.path.join(get_config_dir(), "server.yaml")
    user_settings_file_path = os.path.join(get_config_dir(), "settings.yaml")

    if os.path.isfile(user_settings_file_path) and not os.path.isfile(
        server_settings_file_path
    ):
        shutil.copy(user_settings_file_path, server_settings_file_path)

    settings = get_settings()
    yaml_output = yaml.dump(settings, Dumper=EnumDumper)

    for file_path in (server_settings_file_path, user_settings_file_path):
        with open(file_path, "w") as f:
            f.write(yaml_output)


def down():
    pass
