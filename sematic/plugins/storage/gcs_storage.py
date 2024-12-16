# Standard Library
import enum
import logging
from datetime import timedelta
from typing import Iterable, List, Type

# Third-party
from google.cloud import storage as gcs  # type: ignore

# Sematic
from sematic.abstract_plugin import (
    SEMATIC_PLUGIN_AUTHOR,
    AbstractPlugin,
    AbstractPluginSettingsVar,
    PluginVersion,
)
from sematic.config.settings import get_plugin_setting
from sematic.plugins.abstract_storage import AbstractStorage, StorageDestination
from sematic.utils.memoized_property import memoized_property
from sematic.utils.retry import retry


logger = logging.getLogger(__name__)

_PLUGIN_VERSION = (0, 1, 0)


class GcsClientMethod(enum.Enum):
    PUT = "PUT"
    GET = "GET"


class GcsStorageSettingsVar(AbstractPluginSettingsVar):
    GCP_GCS_BUCKET = "GCP_GCS_BUCKET"


class GcsStorage(AbstractStorage, AbstractPlugin):
    """
    Implementation of the `AbstractStorage` interface for GCP GCS storage. The
    bucket where to store values is determined by the `GCP_GCS_BUCKET` plug-in
    setting.
    """

    PRESIGNED_URL_EXPIRATION = timedelta(minutes=5)

    @staticmethod
    def get_author() -> str:
        return SEMATIC_PLUGIN_AUTHOR

    @staticmethod
    def get_version() -> PluginVersion:
        return _PLUGIN_VERSION

    @classmethod
    def get_settings_vars(cls) -> Type[AbstractPluginSettingsVar]:
        return GcsStorageSettingsVar

    @memoized_property
    def _bucket_str(self) -> str:
        return get_plugin_setting(self.__class__, GcsStorageSettingsVar.GCP_GCS_BUCKET)

    @memoized_property
    def _storage_client(self):
        return gcs.Client()

    @memoized_property
    def _bucket(self) -> gcs.Bucket:
        return self._storage_client.bucket(self._bucket_str)

    def _blob_for_key(self, key: str) -> gcs.Blob:
        return self._bucket.blob(key)

    def _make_presigned_url(self, client_method: GcsClientMethod, key: str) -> str:
        logger.info("Generating GCS presigned url for %s", key)
        presigned_url = self._blob_for_key(key).generate_signed_url(
            expiration=self.PRESIGNED_URL_EXPIRATION,
            method=client_method.value,
            version="v4",
        )

        return presigned_url

    def get_write_destination(self, namespace: str, key: str, _) -> StorageDestination:
        return StorageDestination(
            uri=self._make_presigned_url(GcsClientMethod.PUT, f"{namespace}/{key}"),
        )

    def get_read_destination(self, namespace: str, key: str, _) -> StorageDestination:
        return StorageDestination(
            uri=self._make_presigned_url(GcsClientMethod.GET, f"{namespace}/{key}"),
        )

    @retry(tries=3, delay=5)
    def get_line_stream(self, key: str, encoding: str = "utf8") -> Iterable[str]:
        """Get value from GCS into a stream of text lines.

        Note that currently this implementation is not suitable for large files, as
        the whole file will be downloaded into memory. If large file downloads are
        required, this implementation should be revisited. Currently log files have
        a max size of 1k lines, and thus should be safe to load here.
        """
        # Note: it appears that a new python dependency is needed if we wanted to
        # truly stream this: google-resumable-media.
        blob = self._blob_for_key(key)
        as_bytes = blob.download_as_bytes()
        as_str = str(as_bytes, encoding)
        return as_str.splitlines()

    @retry(tries=3, delay=5)
    def get_child_paths(self, key_prefix: str) -> List[str]:
        """Get all descendants of the 'directory' specified by the prefix.

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

        list_objects_return = self._bucket.list_blobs(
            prefix=key_prefix,
            delimiter="/",
            include_trailing_delimiter=False,
        )

        for blob in list_objects_return:
            if blob.name == key_prefix:
                # don't want the "directory" itself, only its children.
                continue
            keys.append(blob.name)

        return keys
