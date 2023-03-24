# Standard Library
import enum
import logging
from typing import Dict, Iterable, List, Type

# Third-party
import boto3
import botocore.config
import botocore.exceptions

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


class S3ClientMethod(enum.Enum):
    PUT = "put_object"
    GET = "get_object"


class S3StorageSettingsVar(AbstractPluginSettingsVar):
    AWS_S3_BUCKET = "AWS_S3_BUCKET"
    AWS_S3_REGION = "AWS_S3_REGION"


class S3Storage(AbstractStorage, AbstractPlugin):
    """
    Implementation of the `AbstractStorage` interface for AWS S3 storage. The
    bucket where to store values is determined by the `AWS_S3_BUCKET` plug-in
    setting.
    """

    PRESIGNED_URL_EXPIRATION = 5 * 60  # 5 minutes

    @staticmethod
    def get_author() -> str:
        return SEMATIC_PLUGIN_AUTHOR

    @staticmethod
    def get_version() -> PluginVersion:
        return _PLUGIN_VERSION

    @classmethod
    def get_settings_vars(cls) -> Type[AbstractPluginSettingsVar]:
        return S3StorageSettingsVar

    @memoized_property
    def _bucket(self) -> str:
        return get_plugin_setting(self.__class__, S3StorageSettingsVar.AWS_S3_BUCKET)

    @memoized_property
    def _region(self) -> str:
        return get_plugin_setting(self.__class__, S3StorageSettingsVar.AWS_S3_REGION)

    @memoized_property
    def _s3_client(self):
        return boto3.client(
            "s3",
            config=botocore.config.Config(
                region_name=self._region, signature_version="s3v4"
            ),
        )

    def _make_presigned_url(self, client_method: S3ClientMethod, key: str) -> str:
        logger.info("Generating S3 presigned url for %s", key)
        presigned_url = self._s3_client.generate_presigned_url(
            ClientMethod=client_method.value,
            Params={
                "Bucket": self._bucket,
                "Key": key,
                # TODO: Recover caching https://github.com/sematic-ai/sematic/issues/653
                # "ResponseCacheControl": "max-age=31536000, immutable, private",
            },
            ExpiresIn=self.PRESIGNED_URL_EXPIRATION,
        )

        return presigned_url

    def get_write_destination(self, namespace: str, key: str, _) -> StorageDestination:
        return StorageDestination(
            uri=self._make_presigned_url(S3ClientMethod.PUT, f"{namespace}/{key}")
        )

    def get_read_destination(self, namespace: str, key: str, _) -> StorageDestination:
        return StorageDestination(
            uri=self._make_presigned_url(S3ClientMethod.GET, f"{namespace}/{key}")
        )

    @retry(tries=3, delay=5)
    def get_line_stream(self, key: str, encoding: str = "utf8") -> Iterable[str]:
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
