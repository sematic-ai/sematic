# Standard Library
import abc
import io
import os
from typing import Any, Dict, Iterable, List

# Third-party
import boto3
import botocore.exceptions

# Sematic
from sematic.config.config import get_config
from sematic.config.user_settings import UserSettingsVar, get_user_setting
from sematic.utils.memoized_property import memoized_property
from sematic.utils.retry import retry
from sematic.config.settings import MissingSettingsError


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


class LocalStorage(Storage):
    """
    A local storage implementation of the `Storage` interface. Values are stores
    in the data directory of the Sematic directory, typically at
    `~/.sematic/data`.
    """

    def set(self, key: str, value: bytes):
        dir_path = os.path.split(key)[0]
        os.makedirs(os.path.join(get_config().data_dir, dir_path), exist_ok=True)

        with open(os.path.join(get_config().data_dir, key), "wb") as file:
            file.write(value)

    def get(self, key: str) -> bytes:
        try:
            with open(os.path.join(get_config().data_dir, key), "rb") as file:
                return file.read()
        except FileNotFoundError:
            raise NoSuchStorageKey(self, key)


class S3Storage(Storage):
    """
    Implementation of the `Storage` interface for AWS S3 storage. The bucket
    where to store values is determined by the `AWS_S3_BUCKET` user settings variable.
    """

    @memoized_property
    def _bucket(self) -> str:
        return get_user_setting(UserSettingsVar.AWS_S3_BUCKET)

    @memoized_property
    def _endpoint_url(self) -> str:
        try:
            return get_user_setting(UserSettingsVar.AWS_S3_ENDPOINT_URL)
        except MissingSettingsError:
            return None

    @memoized_property
    def _s3_client(self):
        return boto3.client("s3", endpoint_url=self._endpoint_url)

    def set(self, key: str, value: bytes):
        """Store value in S3"""
        with io.BytesIO(value) as file_obj:
            self._s3_client.upload_fileobj(file_obj, self._bucket, key)

    @retry(tries=3, delay=5)
    def get(self, key: str) -> bytes:
        """Get value from S3.

        See TODO in `set`.
        """
        file_obj = io.BytesIO()
        try:
            self._s3_client.download_fileobj(self._bucket, key, file_obj)
        except botocore.exceptions.ClientError as e:
            # Standardizing "Not found" errors across storage backends
            if "404" in str(e):
                raise NoSuchStorageKey(self, key)

            raise e
        return file_obj.getvalue()

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
