# Sematic
from sematic.abstract_plugin import AbstractPlugin, AbstractPluginSettingsVar


class FooPluginSettingsVar(AbstractPluginSettingsVar):
    pass


class FooPlugin(AbstractPlugin):
    @staticmethod
    def get_author() -> str:
        return "The Knights who say ni"

    @staticmethod
    def get_version():
        return (0, 1, 0)

    @classmethod
    def get_settings_vars(cls):
        return FooPluginSettingsVar


def test_plugin_path():
    assert FooPlugin.get_path() == "sematic.tests.test_abstract_plugin.FooPlugin"


def test_name():
    assert FooPlugin.get_name() == "FooPlugin"
