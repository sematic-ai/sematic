# Sematic
from sematic.config.server_settings import (
    ServerSettings,
    ServerSettingsVar,
    get_active_server_settings,
    get_server_setting,
)
from sematic.config.tests.fixtures import mock_settings


def test_get_empty_settings_file():
    with mock_settings({}):
        assert get_active_server_settings() == {}


def test_get_no_settings_file():
    with mock_settings({}):
        assert get_active_server_settings() == {}


def test_get_settings():
    with mock_settings(
        {
            "version": 0,
            "profiles": {
                "default": {
                    "settings": {
                        ServerSettings.get_path(): {
                            ServerSettingsVar.KUBERNETES_NAMESPACE.value: "foobar"
                        }
                    }
                }
            },
        }
    ):
        assert get_server_setting(ServerSettingsVar.KUBERNETES_NAMESPACE) == "foobar"


def test_fresh_start():
    with mock_settings(None):
        assert (
            get_server_setting(ServerSettingsVar.KUBERNETES_NAMESPACE, "default")
            == "default"
        )
