# Standard Library
import abc
import enum
import logging
import os
from typing import Any, Dict, Iterable, List, Type

# Third-party
import boto3
import botocore.exceptions
import requests

# Sematic
from sematic.config.config import get_config
from sematic.config.user_settings import UserSettingsVar, get_user_setting
from sematic.utils.memoized_property import memoized_property
from sematic.utils.retry import retry

logger = logging.getLogger(__name__)


class StorageMode(enum.Enum):
    READ = "read"
    WRITE = "write"


class Storage(abc.ABC):
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
    def __init__(self, storage: Storage, key: str):
        super().__init__(f"No such storage key for {storage.__class__.__name__}: {key}")


class MemoryStorage(Storage):
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


class LocalStorage(Storage):
    """
    A local storage implementation of the `Storage` interface. Values are stores
    in the data directory of the Sematic directory, typically at
    `~/.sematic/data`.
    """

    def set(self, key: str, value: bytes):
        logger.debug(f"{self.__class__.__name__} Setting value for key: {key}")

        dir_path = os.path.split(key)[0]
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


class S3ClientMethod(enum.Enum):
    PUT = "put_object"
    GET = "get_object"


class S3Storage(Storage):
    """
    Implementation of the `Storage` interface for AWS S3 storage. The bucket
    where to store values is determined by the `AWS_S3_BUCKET` user settings variable.
    """

    PRESIGNED_URL_EXPIRATION = 5 * 60  # 5 minutes

    @memoized_property
    def _bucket(self) -> str:
        return get_user_setting(UserSettingsVar.AWS_S3_BUCKET)

    @memoized_property
    def _s3_client(self):
        return boto3.client("s3")

    def _make_presigned_url(self, client_method: S3ClientMethod, key: str) -> str:
        presigned_url = self._s3_client.generate_presigned_url(
            ClientMethod=client_method.value,
            Params={"Bucket": self._bucket, "Key": key},
            ExpiresIn=self.PRESIGNED_URL_EXPIRATION,
        )

        return presigned_url

    def _get_write_location(self, namespace: str, key: str) -> str:
        return self._make_presigned_url(S3ClientMethod.PUT, f"{namespace}/{key}")

    def _get_read_location(self, namespace: str, key: str) -> str:
        return self._make_presigned_url(S3ClientMethod.GET, f"{namespace}/{key}")

    def set(self, key: str, value: bytes):
        """Store value in S3"""
        logger.debug(f"{self.__class__.__name__} Setting value for key: {key}")

        response = requests.put(key, data=value)
        response.raise_for_status()

    @retry(tries=3, delay=5)
    def get(self, key: str) -> bytes:
        """Get value from S3."""
        response = requests.get(key)

        if response.status_code == 404:
            raise NoSuchStorageKey(self, key)

        response.raise_for_status()

        return response.content

    def set_from_file(self, key: str, value_file_path: str):
        """Store value in S3 using the contents of a file

        see TODO in 'set'
        """
        with open(value_file_path, "rb") as file_obj:
            self._s3_client.upload_fileobj(file_obj, self._bucket, key)

    @retry(tries=3, delay=5)
    def get_line_stream(self, key: str, encoding="utf8") -> Iterable[str]:
        """Get value from S3 into a stream of text lines.

        See TODO in `set`.
        """
        try:
            obj = self._s3_client.get_object(Bucket=self._bucket, Key=key)
            return _bytes_buffer_to_text(obj["Body"].iter_lines(), encoding)
        except botocore.exceptions.ClientError as e:
            # Standardizing "Not found" errors across storage backends
            if "404" in str(e):
                raise KeyError("{}: {}".format(key, str(e)))

            raise e

    @retry(tries=3, delay=5)
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
        if not key_prefix.endswith("/"):
            key_prefix = f"{key_prefix}/"

        keys = []
        has_more = True
        continuation_token = None

        while has_more:
            continuation: Dict[str, str] = (
                {}
                if continuation_token is None
                else {"ContinuationToken": continuation_token}  # type: ignore
            )

            list_objects_return = self._s3_client.list_objects_v2(
                Bucket=self._bucket,
                Prefix=key_prefix,
                **continuation,
            )

            has_more = list_objects_return["IsTruncated"]
            continuation_token = list_objects_return.get("NextContinuationToken")

            for obj in list_objects_return.get("Contents", []):
                keys.append(obj["Key"])

        return keys


def _bytes_buffer_to_text(bytes_buffer: Iterable[bytes], encoding) -> Iterable[str]:
    for line in bytes_buffer:
        yield str(line, encoding=encoding)


class StorageSettingValue(enum.Enum):
    """
    Possible value for the SEMATIC_STORAGE setting.
    """

    LOCAL = "LOCAL"
    MEMORY = "MEMORY"
    S3 = "S3"


# This and StorageSettingValue should be replaced by a proper
# plugin-registry
_STORAGE_ENGINE_REGISTRY: Dict[StorageSettingValue, Type[Storage]] = {
    StorageSettingValue.LOCAL: LocalStorage,
    StorageSettingValue.MEMORY: MemoryStorage,
    StorageSettingValue.S3: S3Storage,
}


def get_storage(storage_setting: StorageSettingValue) -> Type[Storage]:
    return _STORAGE_ENGINE_REGISTRY[storage_setting]
