# Standard Library
import tempfile
from unittest.mock import PropertyMock, patch

# Third-party
import pytest
import yaml

# Sematic
import sematic.config.user_settings
from sematic.config.user_settings import (
    UserSettingsVar,
    get_active_user_settings,
    get_user_setting,
)


@pytest.fixture(scope="function")
def settings_file():
    with tempfile.NamedTemporaryFile() as tf:
        with patch(
            "sematic.config.user_settings.SettingsScope.settings_file_path",
            return_value=tf.name,
            new_callable=PropertyMock,
        ):
            current_settings = (
                sematic.config.user_settings._USER_SETTINGS_SCOPE._settings
            )
            sematic.config.user_settings._USER_SETTINGS_SCOPE._settings = None
            sematic.config.user_settings._USER_SETTINGS_SCOPE._active_settings = None

            yield tf

            sematic.config.user_settings._USER_SETTINGS_SCOPE._settings = (
                current_settings
            )
            sematic.config.user_settings._USER_SETTINGS_SCOPE._active_settings = None


def test_get_empty_settings(settings_file):
    assert get_active_user_settings() == {}


def test_get_settings(settings_file):
    settings = {"default": {UserSettingsVar.SNOWFLAKE_USER.value: "foobar"}}
    yaml_output = yaml.dump(settings, Dumper=yaml.Dumper)
    settings_file.write(bytes(yaml_output, encoding="utf-8"))
    settings_file.flush()
    assert get_user_setting(UserSettingsVar.SNOWFLAKE_USER) == "foobar"


def test_fresh_start():
    with tempfile.TemporaryDirectory() as td:
        with patch(
            "sematic.config.settings.get_config_dir",
            return_value=td,
            new_callable=PropertyMock,
        ):
            assert get_active_user_settings() == {}
