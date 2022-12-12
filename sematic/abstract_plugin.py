"""
Module that holds the base abstractions for Sematic's plug-in system.

Plug-ins are classes that inherit from the AbstractPlugin abstract base class.

Plug-ins are imported at runtime based on user's or server's settings stored in
their corresponding yaml files.
"""
# Standard Library
import abc
import enum
import logging
import sys
from importlib import import_module
from typing import Type, final

logger = logging.getLogger(__name__)


class PluginScope(enum.Enum):
    """
    Enum of available plugin scopes.

    At this time plug-ins are supported for artifact storage and authentication.

    This enum is expected to be updated as more plug-in scopes are supported.
    """

    # Storage plug-in scope for artifact data, future pickles, etc.
    STORAGE = "STORAGE"

    # Server-side authentication plug-in scope
    AUTH = "AUTH"


class AbstractPlugin(abc.ABC):
    """
    Abstract base class for plugins.

    All plug-ins must inherit from this class.
    """

    @staticmethod
    @abc.abstractmethod
    def get_author() -> str:
        """
        The plug-in's author.

        Can be an arbitrary string containing contact info (e.g. GitHub profile,
        email address, etc.)
        """
        pass

    @final
    @classmethod
    def get_name(cls) -> str:
        """
        The plug-in's name.

        This is used as a key to store plug-in specific settings in settings
        YAML files.
        """
        return cls.__name__

    @final
    @classmethod
    def get_path(cls) -> str:
        """
        Full import path of the module.

        Can be used in server-returned payloads to tell client code what plug-in
        to use (e.g. server-prescribed upload locations),
        """
        return ".".join([cls.__module__, cls.__name__])


class MissingPluginError(Exception):
    """
    Exception to indicate a missing plug-in.
    """

    pass


def import_plugin(plugin_import_path: str) -> Type[AbstractPlugin]:
    """
    The internal API to import a plug-in based on its import path.

    Parameters
    ----------
    plugin_import_path: str
        fully-qualified import path: some.module.PluginClass

    Raises
    ------
    MissingPluginError
        The requested plug-in cannot be found.
    """
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
