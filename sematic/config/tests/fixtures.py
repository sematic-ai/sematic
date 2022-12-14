# Standard Library
import os
import tempfile
from contextlib import contextmanager
from unittest.mock import patch

# Third-party
import yaml

# Sematic
from sematic.config.settings import _clear_cache


@contextmanager
def mock_settings(settings_dict):
    with tempfile.TemporaryDirectory() as td:
        with patch(
            "sematic.config.settings.get_config_dir",
            return_value=td,
        ):
            settings_file_path = os.path.join(td, "settings.yaml")
            if settings_dict is not None:
                with open(settings_file_path, "w") as settings_file:
                    yaml.dump(settings_dict, settings_file)

            _clear_cache()

            yield settings_file_path

            _clear_cache()
