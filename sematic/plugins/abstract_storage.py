# Standard Library
import abc
import enum
from dataclasses import dataclass
from typing import Any, Type


class PayloadType(enum.Enum):
    URL = "URL"
    BYTES = "BYTES"


@dataclass
class ReadPayload:
    type_: PayloadType
    content: Any


class AbstractStorage(abc.ABC):
    """
    Abstract base class to represent a key/value storage engine.
    """

    @abc.abstractmethod
    def get_write_location(self, namespace: str, key: str) -> str:
        """
        Gets write location for namespace/key.

        This is a server-side API. It is used to return write locations to the resolver.

        This is expected to be a URL which clients will PUT to.
        """
        pass

    @abc.abstractmethod
    def get_read_payload(self, namespace: str, key: str) -> ReadPayload:
        """
        Get a read payload for namespace/key.

        This is a server-side API. It is used to return data to the resolver.
        The returned payload can be a URL to redirect to (PayloadType.URL) or a
        binary content to return as is to the resolver (PayloadType.BYTES).
        """
        pass


class NoSuchStorageKeyError(KeyError):
    def __init__(self, storage: Type[AbstractStorage], key: str):
        super().__init__(f"No such storage key for {storage.__name__}: {key}")
