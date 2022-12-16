# Standard Library
import logging
import os

# Sematic
from sematic.abstract_plugin import AbstractPlugin, PluginVersion
from sematic.config.config import get_config
from sematic.plugins.abstract_storage import AbstractStorage, NoSuchStorageKey

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

    def get(self, key: str) -> bytes:
        try:
            with open(os.path.join(get_config().data_dir, key), "rb") as file:
                return file.read()
        except FileNotFoundError:
            raise NoSuchStorageKey(self, key)

    def _get_write_location(self, namespace: str, key: str) -> str:
        return os.path.join(get_config().data_dir, namespace, key)

    def _get_read_location(self, namespace: str, key: str) -> str:
        return f"sematic:///data/{namespace}/{key}"
