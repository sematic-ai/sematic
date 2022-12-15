# Third-party
import pytest

# Sematic
from sematic.abstract_plugin import (
    AbstractPlugin,
    AbstractPluginSettingsVar,
    PluginScope,
)
from sematic.config.settings import (
    _DEFAULT_PROFILE,
    MissingSettingsError,
    get_active_plugins,
    get_active_settings,
    get_plugin_setting,
    get_plugin_settings,
    get_settings,
)
from sematic.config.tests.fixtures import mock_settings


class SettingsVar(AbstractPluginSettingsVar):
    SOME_SETTING = "SOME_SETTING"
    OTHER_SETTING = "OTHER_SETTING"


class TestPlugin(AbstractPlugin):
    @staticmethod
    def get_author() -> str:
        return "The Knights who say ni"

    @staticmethod
    def get_version():
        return (0, 1, 0)

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
                    TestPlugin.get_path(): {SettingsVar.SOME_SETTING.value: "bar"}
                },
            }
        },
    }
    with mock_settings(test_settings) as settings_file_name:
        yield settings_file_name


def test_get_active_plugins(plugin_settings):
    assert get_active_plugins(scope=PluginScope.STORAGE, default=[]) == [TestPlugin]
    assert get_active_plugins(scope=PluginScope.AUTH, default=[]) == []


def test_get_active_settings(plugin_settings):
    active_settings = get_active_settings()

    assert active_settings.scopes == {PluginScope.STORAGE: [TestPlugin.get_path()]}

    assert active_settings.settings == {
        TestPlugin.get_path(): {SettingsVar.SOME_SETTING: "bar"}
    }


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
        TestPlugin.get_path(): {SettingsVar.SOME_SETTING: "bar"}
    }


@pytest.fixture
def no_settings_file():
    with mock_settings(None):
        yield


def test_from_scratch(no_settings_file):
    settings = get_settings()

    assert settings.version == 1

    settings_profile = settings.profiles[_DEFAULT_PROFILE]

    assert settings_profile.scopes == {}

    assert settings_profile.settings == {}

    assert get_active_plugins(scope=PluginScope.STORAGE, default=[TestPlugin]) == [
        TestPlugin
    ]

    assert (
        get_plugin_setting(TestPlugin, SettingsVar.SOME_SETTING, "default") == "default"
    )
