# Standard Library
import os
import shutil

# Sematic
from sematic.config.server_settings import get_server_settings_scope
from sematic.config.user_settings import get_user_settings_scope


def up():
    server_settings_file_path = get_server_settings_scope().settings_file_path
    user_settings_file_path = get_user_settings_scope().settings_file_path

    if os.path.isfile(user_settings_file_path) and not os.path.isfile(
        server_settings_file_path
    ):
        shutil.copy(user_settings_file_path, server_settings_file_path)


def down():
    pass
