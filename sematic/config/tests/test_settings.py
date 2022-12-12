# Standard Library
import os
import tempfile
import uuid
from contextlib import contextmanager
from unittest.mock import patch

# Third-party
import yaml

# Sematic
from sematic.abstract_plugin import AbstractPlugin, PluginScope
from sematic.config.settings import (
    PLUGINS_SETTINGS_KEY,
    AbstractSettingsVar,
    SettingsScope,
)


class TestSettingsVar(AbstractSettingsVar):
    SOME_SETTING = "SOME_SETTING"

    plugins = "plugins"


class TestPlugin(AbstractPlugin):
    @staticmethod
    def get_author() -> str:
        return "The Knights who say ni"

    @staticmethod
    def get_version():
        return (0, 1, 0)


@contextmanager
def settings(settings_dict):
    with tempfile.TemporaryDirectory() as td:
        with patch(
            "sematic.config.settings.get_config_dir",
            return_value=td,
            # new_callable=PropertyMock,
        ):
            settings_file_name = uuid.uuid4().hex
            with open(os.path.join(td, settings_file_name), "w") as settings_file:
                yaml.dump(settings_dict, settings_file)

            yield settings_file_name


def test_plugins_scopes():
    test_settings = {
        "default": {
            "SOME_SETTING": "foo",
            "plugins": {
                "scopes": {PluginScope.STORAGE.value: [TestPlugin.get_path()]},
                "settings": {TestPlugin.get_name(): {"TEST_PLUGIN_SETTING": "bar"}},
            },
        }
    }
    with settings(test_settings) as settings_file_name:
        settings_scope = SettingsScope(
            file_name=settings_file_name, cli_command="foo", vars=TestSettingsVar
        )

        selected_plugins = settings_scope.get_selected_plugins(
            scope=PluginScope.STORAGE, default=[], var=TestSettingsVar.plugins
        )

        assert selected_plugins == [TestPlugin]

        test_plugin_settings = settings_scope.get_plugin_settings(
            TestSettingsVar.plugins
        )

        assert test_plugin_settings[PLUGINS_SETTINGS_KEY] == {
            TestPlugin.get_name(): {"TEST_PLUGIN_SETTING": "bar"}
        }

        os.environ["TEST_PLUGIN_SETTING"] = "CLI_OVERRIDE"

        assert settings_scope.get_plugin_settings(TestSettingsVar.plugins)[
            PLUGINS_SETTINGS_KEY
        ] == {TestPlugin.get_name(): {"TEST_PLUGIN_SETTING": "CLI_OVERRIDE"}}

        auth_plugins = settings_scope.get_selected_plugins(
            scope=PluginScope.AUTH, default=[], var=TestSettingsVar.plugins
        )

        assert auth_plugins == []


def test_from_scratch():
    settings_scope = SettingsScope(
        file_name=uuid.uuid4().hex, cli_command="foo", vars=TestSettingsVar
    )

    assert (
        settings_scope.get_selected_plugins(
            PluginScope.STORAGE, default=[], var=TestSettingsVar.plugins
        )
        == []
    )

    assert settings_scope.get_plugin_settings(TestSettingsVar.plugins) == {
        "scopes": {},
        "settings": {},
    }
