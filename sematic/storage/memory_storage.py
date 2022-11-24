# Standard Library
from typing import Any, Dict

# Sematic
from sematic.abstract_storage import AbstractStorage, NoSuchStorageKey
from sematic.plugins import AbstractPlugin, PluginScope, register_plugin


@register_plugin(scope=PluginScope.STORAGE, author="github.com/sematic-ai")
class MemoryStorage(AbstractStorage, AbstractPlugin):
    """
    An in-memory key/value store implementing the `Storage` interface.
    """

    def __init__(self):
        self._store: Dict[str, Any] = {}

    def set(self, key: str, value: bytes):
        self._store[key] = value

    def get(self, key: str) -> bytes:
        try:
            return self._store[key]
        except KeyError:
            raise NoSuchStorageKey(self, key)

    def _get_write_location(self, namespace, key: str) -> str:
        return f"{namespace}/{key}"

    def _get_read_location(self, namespace: str, key: str) -> str:
        return self._get_write_location(namespace, key)
