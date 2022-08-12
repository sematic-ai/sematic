# Standard Library
import tempfile
from unittest.mock import PropertyMock, patch

# Third-party
import pytest
import yaml

# Sematic
import sematic.user_settings
from sematic.user_settings import SettingsVar, get_all_user_settings, get_user_settings


@pytest.fixture(scope="function")
def settings_file():
    with tempfile.NamedTemporaryFile() as tf:
        with patch(
            "sematic.user_settings._settings_file",
            return_value=tf.name,
            new_callable=PropertyMock,
        ):
            current_settings = sematic.user_settings._settings
            sematic.user_settings._settings = None

            yield tf

            sematic.user_settings._settings = current_settings


def test_get_empty_settings(settings_file):
    assert get_all_user_settings() == {}


def test_get_settings(settings_file):
    settings = {"default": {"SNOWFLAKE_USER": "foobar"}}
    yaml_output = yaml.dump(settings, Dumper=yaml.Dumper)
    settings_file.write(bytes(yaml_output, encoding="utf-8"))
    settings_file.flush()
    assert get_all_user_settings() == settings["default"]
    assert get_user_settings(SettingsVar.SNOWFLAKE_USER) == "foobar"
