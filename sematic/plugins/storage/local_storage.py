# Standard Library
import logging
import os

# Sematic
from sematic.abstract_plugin import AbstractPlugin, PluginVersion
from sematic.config.config import get_config
from sematic.plugins.abstract_storage import (
    AbstractStorage,
    NoSuchStorageKey,
    PayloadType,
    ReadPayload,
)

logger = logging.getLogger(__name__)

_PLUGIN_VERSION = (0, 1, 0)


class LocalStorage(AbstractStorage, AbstractPlugin):
    """
    A local storage implementation of the `AbstractStorage` interface. Values
    are stores in the data directory of the Sematic directory, typically at
    `~/.sematic/data`.
    """

    @staticmethod
    def get_author() -> str:
        return "github.com/sematic-ai"

    @staticmethod
    def get_version() -> PluginVersion:
        return _PLUGIN_VERSION

    def set(self, key: str, value: bytes):
        logger.debug(f"{self.__class__.__name__} Setting value for key: {key}")

        dir_path = os.path.dirname(key)
        os.makedirs(dir_path, exist_ok=True)

        with open(key, "wb") as file:
            file.write(value)

    def get_write_location(self, namespace: str, key: str) -> str:
        # return os.path.join(get_config().data_dir, namespace, key)
        return f"/api/v1/upload/{namespace}/{key}"

    def get_read_payload(self, namespace: str, key: str) -> ReadPayload:
        try:
            with open(self.get_write_location(namespace, key), "rb") as file:
                content = file.read()
        except FileNotFoundError:
            raise NoSuchStorageKey(self, key)

        return ReadPayload(type_=PayloadType.BYTES, content=content)
