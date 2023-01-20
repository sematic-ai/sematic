# Standard Library
import os
import tempfile
from contextlib import contextmanager
from typing import Any, Dict, Optional
from unittest.mock import patch

# Third-party
import yaml

# Sematic
import sematic.config.server_settings as server_settings_module
import sematic.config.settings as settings_module
import sematic.config.user_settings as user_settings_module

EXPECTED_DEFAULT_ACTIVE_SETTINGS = settings_module.ProfileSettings(
    scopes={},
    settings={
        server_settings_module.ServerSettings.get_path(): {},
        user_settings_module.UserSettings.get_path(): {},
    },
)


@contextmanager
def mock_settings(settings_dict: Optional[Dict[str, Any]]):
    """
    Returns the path to a mock settings file.

    If the `settings_dict` parameter is empty, the settings file will be initialized with
    an empty structure. If it is None, the file will not exist.
    """
    with tempfile.TemporaryDirectory() as td:
        with patch(
            "sematic.config.settings.get_config_dir",
            return_value=td,
        ):
            settings_file_path = os.path.join(td, "settings.yaml")
            if settings_dict is not None:
                with open(settings_file_path, "w") as settings_file:
                    yaml.dump(
                        settings_dict, settings_file, Dumper=settings_module.EnumDumper
                    )

            _clear_cache()

            yield settings_file_path

            _clear_cache()


def _clear_cache():
    settings_module._SETTINGS = None
    settings_module._ACTIVE_SETTINGS = None
