# Sematic
from sematic.abstract_plugin import AbstractPlugin


class TestPlugin(AbstractPlugin):
    @staticmethod
    def get_author() -> str:
        return "The Knights who say ni"


def test_plugin_path():
    assert TestPlugin.get_path() == "sematic.tests.test_abstract_plugin.TestPlugin"


def test_name():
    assert TestPlugin.get_name() == "TestPlugin"
