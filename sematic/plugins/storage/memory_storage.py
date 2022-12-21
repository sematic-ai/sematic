# Standard Library
from typing import Any, Dict

# Sematic
from sematic.abstract_plugin import AbstractPlugin, PluginVersion
from sematic.plugins.abstract_storage import (
    AbstractStorage,
    NoSuchStorageKey,
    PayloadType,
    ReadPayload,
)

_PLUGIN_VERSION = (0, 1, 0)


class MemoryStorage(AbstractStorage, AbstractPlugin):
    """
    An in-memory key/value store implementing the `AbstractStorage` interface.

    This is only usable if both resolver and server are in the same Python
    process, i.e. only in a unit test.
    """

    @staticmethod
    def get_author() -> str:
        return "github.com/sematic-ai"

    @staticmethod
    def get_version() -> PluginVersion:
        return _PLUGIN_VERSION

    def __init__(self):
        self._store: Dict[str, Any] = {}

    def set(self, key: str, value: bytes):
        self._store[key] = value

    def get(self, key: str) -> bytes:
        try:
            return self._store[key]
        except KeyError:
            raise NoSuchStorageKey(self, key)

    def get_write_location(self, namespace, key: str) -> str:
        return f"{namespace}/{key}"

    def get_read_payload(self, namespace: str, key: str) -> ReadPayload:
        try:
            content = self._store[self.get_write_location(namespace, key)]
        except KeyError:
            raise NoSuchStorageKey(self, key)

        return ReadPayload(type_=PayloadType.BYTES, content=content)
