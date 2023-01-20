# Sematic
from sematic.config.tests.fixtures import mock_settings
from sematic.config.user_settings import (
    UserSettings,
    UserSettingsVar,
    get_active_user_settings,
    get_user_setting,
)


def test_get_empty_settings_file():
    with mock_settings({}):
        assert get_active_user_settings() == {}


def test_get_no_settings_file():
    with mock_settings(None):
        assert get_active_user_settings() == {}


def test_get_settings():
    with mock_settings(
        {
            "version": 0,
            "profiles": {
                "default": {
                    "settings": {
                        UserSettings.get_path(): {
                            UserSettingsVar.SNOWFLAKE_USER.value: "foobar"
                        }
                    }
                }
            },
        }
    ):
        assert get_user_setting(UserSettingsVar.SNOWFLAKE_USER) == "foobar"


def test_fresh_start():
    with mock_settings(None):
        assert get_user_setting(UserSettingsVar.SNOWFLAKE_USER, "default") == "default"
