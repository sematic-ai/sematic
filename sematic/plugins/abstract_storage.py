# Standard Library
import abc
import enum


class StorageMode(enum.Enum):
    READ = "read"
    WRITE = "write"


class AbstractStorage(abc.ABC):
    """
    Abstract base class to represent a key/value storage engine.
    """

    @abc.abstractmethod
    def set(self, key: str, value: bytes):
        """
        Sets value for key.
        """
        pass

    @abc.abstractmethod
    def get(self, key: str) -> bytes:
        """
        Gets value for key.
        """
        pass

    @abc.abstractmethod
    def _get_write_location(self, namespace: str, key: str) -> str:
        pass

    @abc.abstractmethod
    def _get_read_location(self, namespace: str, key: str) -> str:
        pass

    def get_location(self, namespace: str, key: str, mode: StorageMode) -> str:
        if mode == StorageMode.READ:
            return self._get_read_location(namespace, key)

        if mode == StorageMode.WRITE:
            return self._get_write_location(namespace, key)

        raise KeyError(f"Unknown storage mode: {mode}")


class NoSuchStorageKey(KeyError):
    def __init__(self, storage: AbstractStorage, key: str):
        super().__init__(f"No such storage key for {storage.__class__.__name__}: {key}")
