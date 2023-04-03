# Standard Library
import abc
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Type, cast

# Sematic
from sematic.abstract_plugin import AbstractPlugin, PluginScope
from sematic.config.settings import get_active_plugins
from sematic.db.models.user import User


@dataclass
class StorageDestination:
    uri: str
    request_headers: Dict[str, str] = field(default_factory=dict)


class AbstractStorage(abc.ABC):
    """
    Abstract base class to represent a key/value storage engine.
    """

    @abc.abstractmethod
    def get_write_destination(
        self, namespace: str, key: str, user: Optional[User]
    ) -> StorageDestination:
        """
        Gets write location for namespace/key.

        This is a server-side API. It is used to return write locations to the resolver.

        This is expected to be a URL which clients will PUT to.
        """
        pass

    @abc.abstractmethod
    def get_read_destination(
        self, namespace: str, key: str, user: Optional[User]
    ) -> StorageDestination:
        """
        Get a read payload for namespace/key.

        This is a server-side API. It is used to return data to the resolver.
        The returned payload can be a URL to redirect to (PayloadType.URL) or a
        binary content to return as is to the resolver (PayloadType.BYTES).
        """
        pass

    @abc.abstractmethod
    def get_child_paths(self, key_prefix: str) -> List[str]:
        """Get all descendants of the 'directory' specified by the prefix
        Parameters
        ----------
        key_prefix:
            The prefix to a key that would be used with 'get' or 'set'. The keys are
            treated as being like directories, with '/' in a key specifying an
            organizational unit for the objects.
        Returns
        -------
        A list of all keys that start with the prefix. You can think of this as getting
        the absolute file paths for all contents of a directory (including 'files' in
        'subdirectories').
        """
        pass

    @abc.abstractmethod
    def get_line_stream(self, key: str, encoding: str = "utf8") -> Iterable[str]:
        """
        Get value in stream of text lines.
        """
        pass


class NoSuchStorageKeyError(KeyError):
    def __init__(self, storage: Type[AbstractStorage], key: str):
        super().__init__(f"No such storage key for {storage.__name__}: {key}")


def get_storage_plugins(
    default: List[Type[AbstractPlugin]],
) -> List[Type[AbstractStorage]]:
    """
    Return all configured "STORAGE" scope plugins.
    """
    storage_plugins = get_active_plugins(PluginScope.STORAGE, default=default)

    storage_classes = [
        cast(Type[AbstractStorage], plugin) for plugin in storage_plugins
    ]

    return storage_classes
