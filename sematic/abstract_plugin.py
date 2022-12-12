# Standard Library
import abc
import enum
import logging
import sys
from importlib import import_module
from typing import Type

logger = logging.getLogger(__name__)


class PluginScope(enum.Enum):
    STORAGE = "STORAGE"
    AUTH = "AUTH"


class AbstractPlugin(abc.ABC):
    @staticmethod
    @abc.abstractmethod
    def get_author() -> str:
        pass

    @classmethod
    def get_name(cls) -> str:
        return cls.__name__

    @classmethod
    def get_path(cls) -> str:
        return ".".join([cls.__module__, cls.__name__])


class MissingPluginError(Exception):
    pass


def import_plugin(plugin_import_path: str) -> Type[AbstractPlugin]:
    try:
        split_import_path = plugin_import_path.split(".")
        import_path, plugin_name = (
            ".".join(split_import_path[:-1]),
            split_import_path[-1],
        )
    except (AttributeError, IndexError):
        raise ValueError(f"Incorrect plugin import path: {plugin_import_path}")

    try:
        if import_path not in sys.modules:
            logger.info("Importing plugin %s", plugin_import_path)

        # module imports are cached so this is idempotent (i.e. no need to be in
        # the if statement above)
        module = import_module(import_path)
        plugin = getattr(module, plugin_name)
    except (ImportError, AttributeError):
        raise MissingPluginError(plugin_import_path)

    return plugin
