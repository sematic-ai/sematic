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
from typing import Tuple, Type, final

logger = logging.getLogger(__name__)


class PluginScope(enum.Enum):
    """
    Enum of available plugin scopes.

    At this time plug-ins are supported for artifact storage and authentication.

    This enum is expected to be updated as more plug-in scopes are supported.
    """

    # Core plug-in scope. Will only ever have a single plug-in.
    # This is useful to keep core settings symmetrical with plug-in settings
    SEMATIC = "SEMATIC"

    # Storage plug-in scope for artifact data, future pickles, etc.
    STORAGE = "STORAGE"

    # Server-side authentication plug-in scope
    AUTH = "AUTH"


class AbstractPluginSettingsVar(enum.Enum):
    """
    Abstract base class for lists of settings vars
    """

    pass


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

    @staticmethod
    @abc.abstractmethod
    def get_version() -> Tuple[int, int, int]:
        """
        Plug-in version: MAJOR.MINOR.PATCH

        increment PATCH for bug fixes
        increment MINOR for new functionalities
        increment MAJOR for breaking API changes (0 means unstable)
        """
        pass

    @classmethod
    @abc.abstractmethod
    def get_settings_vars(cls) -> Type[AbstractPluginSettingsVar]:
        """
        Returns the Settings var enum for this plug-in.

        The class must inherit from `AbstractPluginSettingsVar` and list all
        available settings for this plug-in.
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

    def __init__(self, plugin_path: str):
        message = f"Unable to find plug-in {plugin_path}. Module or class is missing."
        super().__init__(message)


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
        first_import = import_path not in sys.modules

        # module imports are cached so this is idempotent
        module = import_module(import_path)
        plugin: Type[AbstractPlugin] = getattr(module, plugin_name)

        if first_import:
            logger.info(
                "Imported plugin %s, version %s",
                plugin.get_path(),
                plugin.get_version(),
            )

    except (ImportError, AttributeError):
        raise MissingPluginError(plugin_import_path)

    return plugin
