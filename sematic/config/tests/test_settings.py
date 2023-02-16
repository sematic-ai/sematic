# Third-party
import pytest

# Sematic
from sematic.abstract_plugin import (
    AbstractPlugin,
    AbstractPluginSettingsVar,
    PluginScope,
)
from sematic.config.server_settings import ServerSettings, ServerSettingsVar
from sematic.config.settings import (
    _DEFAULT_PROFILE,
    _PLUGIN_VERSION_KEY,
    MissingSettingsError,
    get_active_plugins,
    get_active_settings,
    get_plugin_setting,
    get_plugin_settings,
    get_settings,
)
from sematic.config.tests.fixtures import (
    EXPECTED_DEFAULT_ACTIVE_SETTINGS,
    mock_settings,
)
from sematic.config.user_settings import UserSettings, UserSettingsVar
from sematic.tests.fixtures import environment_variables


class SettingsVar(AbstractPluginSettingsVar):
    SOME_SETTING = "SOME_SETTING"
    OTHER_SETTING = "OTHER_SETTING"


class TestPlugin(AbstractPlugin):
    @staticmethod
    def get_author() -> str:
        return "The Knights who say ni"

    @staticmethod
    def get_version():
        return 0, 1, 0

    @classmethod
    def get_settings_vars(cls):
        return SettingsVar


@pytest.fixture
def plugin_settings():
    test_settings = {
        "version": 1,
        "profiles": {
            "default": {
                "scopes": {PluginScope.STORAGE.value: [TestPlugin.get_path()]},
                "settings": {
                    TestPlugin.get_path(): {
                        SettingsVar.SOME_SETTING.value: "bar",
                        _PLUGIN_VERSION_KEY: "0.1.0",
                    }
                },
            }
        },
    }
    with mock_settings(test_settings) as settings_file_name:
        yield settings_file_name


def test_get_plugin_setting(plugin_settings):
    assert get_plugin_setting(TestPlugin, SettingsVar.SOME_SETTING) == "bar"
    assert (
        get_plugin_setting(TestPlugin, SettingsVar.OTHER_SETTING, "default")
        == "default"
    )
    with pytest.raises(MissingSettingsError):
        get_plugin_setting(TestPlugin, SettingsVar.OTHER_SETTING)


def test_get_plugin_settings(plugin_settings):
    assert get_plugin_settings(TestPlugin) == {SettingsVar.SOME_SETTING: "bar"}


def test_get_settings(plugin_settings):
    settings = get_settings()

    assert settings.version == 1
    settings_profile = settings.profiles[_DEFAULT_PROFILE]

    assert settings_profile.scopes == {PluginScope.STORAGE: [TestPlugin.get_path()]}

    assert settings_profile.settings == {
        TestPlugin.get_path(): {
            SettingsVar.SOME_SETTING: "bar",
            _PLUGIN_VERSION_KEY: "0.1.0",
        }
    }


def test_get_active_plugins(plugin_settings):
    assert get_active_plugins(scope=PluginScope.STORAGE, default=[]) == [TestPlugin]
    assert get_active_plugins(scope=PluginScope.AUTH, default=[]) == []


def test_get_active_settings(plugin_settings):
    active_settings = get_active_settings()

    assert active_settings.scopes == {PluginScope.STORAGE: [TestPlugin.get_path()]}

    assert active_settings.settings == {
        TestPlugin.get_path(): {
            SettingsVar.SOME_SETTING: "bar",
            _PLUGIN_VERSION_KEY: "0.1.0",
        },
        ServerSettings.get_path(): {},
        UserSettings.get_path(): {},
    }


def test_get_active_settings_user_missing(plugin_settings):
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
        active_settings = get_active_settings()

        assert active_settings.scopes == {}
        assert active_settings.settings == {
            ServerSettings.get_path(): {
                ServerSettingsVar.KUBERNETES_NAMESPACE: "foobar"
            },
            UserSettings.get_path(): {},
        }


def test_get_active_settings_server_missing(plugin_settings):
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
        active_settings = get_active_settings()

        assert active_settings.scopes == {}
        assert active_settings.settings == {
            ServerSettings.get_path(): {},
            UserSettings.get_path(): {UserSettingsVar.SNOWFLAKE_USER: "foobar"},
        }


@pytest.fixture
def empty_settings_file():
    with mock_settings({}):
        yield


def test_get_empty_file(empty_settings_file):
    settings = get_settings()
    assert settings.version == 1

    settings_profile = settings.profiles[_DEFAULT_PROFILE]
    assert settings_profile.scopes == {}
    assert settings_profile.settings == {}


def test_get_specific_plugin_empty_file(empty_settings_file):
    get_settings()

    assert get_active_plugins(scope=PluginScope.STORAGE, default=[TestPlugin]) == [
        TestPlugin,
    ]
    assert (
        get_plugin_setting(TestPlugin, SettingsVar.SOME_SETTING, "default") == "default"
    )


def test_env_override_specific_plugin_empty_file(empty_settings_file):
    with environment_variables({"SOME_SETTING": "override"}):
        assert get_plugin_setting(TestPlugin, SettingsVar.SOME_SETTING) == "override"


def test_env_override_absent_plugin_empty_file(empty_settings_file):
    with environment_variables({"SOME_SETTING": "override"}):
        active_settings = get_active_settings()

        # the plugin is not present in the scope, so its variables won't be even loaded
        assert active_settings == EXPECTED_DEFAULT_ACTIVE_SETTINGS


def test_get_active_settings_empty_file(empty_settings_file):
    active_settings = get_active_settings()
    assert active_settings == EXPECTED_DEFAULT_ACTIVE_SETTINGS


@pytest.fixture
def no_settings_file():
    with mock_settings(None):
        yield


def test_get_no_file(no_settings_file):
    settings = get_settings()
    assert settings.version == 1

    settings_profile = settings.profiles[_DEFAULT_PROFILE]
    assert settings_profile.scopes == {}
    assert settings_profile.settings == {}


def test_get_specific_plugin_no_file(no_settings_file):
    get_settings()

    assert get_active_plugins(scope=PluginScope.STORAGE, default=[TestPlugin]) == [
        TestPlugin
    ]
    assert (
        get_plugin_setting(TestPlugin, SettingsVar.SOME_SETTING, "default") == "default"
    )


def test_env_override_specific_plugin_no_file(no_settings_file):
    with environment_variables({"SOME_SETTING": "override"}):
        # when asking for the plugin specifically,
        # its variables will be loaded, and overridden
        assert get_plugin_setting(TestPlugin, SettingsVar.SOME_SETTING) == "override"


def test_env_override_absent_plugin_no_file(no_settings_file):
    with environment_variables({"SOME_SETTING": "override"}):
        active_settings = get_active_settings()

        # the plugin is not present in the scope, so its variables won't be even loaded
        assert active_settings == EXPECTED_DEFAULT_ACTIVE_SETTINGS


def test_get_active_settings_no_file(no_settings_file):
    active_settings = get_active_settings()
    assert active_settings == EXPECTED_DEFAULT_ACTIVE_SETTINGS
