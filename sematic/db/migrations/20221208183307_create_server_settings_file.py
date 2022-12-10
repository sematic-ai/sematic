# Standard Library
import os
import shutil

# Sematic
from sematic.config.server_settings import get_server_settings_scope
from sematic.config.user_settings import get_user_settings_scope


def up():
    server_settings_scope = get_server_settings_scope()
    user_settings_scope = get_user_settings_scope()

    server_settings_file_path = server_settings_scope.settings_file_path
    user_settings_file_path = user_settings_scope.settings_file_path

    if os.path.isfile(user_settings_file_path) and not os.path.isfile(
        server_settings_file_path
    ):
        shutil.copy(user_settings_file_path, server_settings_file_path)

    # Pruning user settings from server file
    server_settings = server_settings_scope.get_settings()
    server_settings_scope.save_settings(server_settings)

    # Pruning server settings from user file
    user_settings = user_settings_scope.get_settings()
    user_settings_scope.save_settings(user_settings)


def down():
    pass
