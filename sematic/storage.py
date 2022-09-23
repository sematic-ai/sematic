# Standard Library
import io
from typing import BinaryIO, List

# Third-party
import boto3
import botocore.exceptions

# Sematic
from sematic.user_settings import SettingsVar, get_user_settings
from sematic.utils.retry import retry


def _get_bucket() -> str:
    return get_user_settings(SettingsVar.AWS_S3_BUCKET)


def set(key: str, value: bytes):
    """Store value in S3

    TODO: modularize the F out of this to enable local/remote storage switch
    based on resolver. Also enable multiple storage clients (AWS, GCP, Azure)
    """
    s3_client = boto3.client("s3")

    with io.BytesIO(value) as file_obj:
        s3_client.upload_fileobj(file_obj, _get_bucket(), key)


def set_from_file(key: str, value_file_path: str):
    """Store value in S3 using the contents of a file

    see TODO in 'set'
    """
    s3_client = boto3.client("s3")

    with open(value_file_path, "rb") as file_obj:
        s3_client.upload_fileobj(file_obj, _get_bucket(), key)


def get(key: str) -> bytes:
    """Get value from S3.

    See TODO in `set`.
    """
    file_obj = io.BytesIO()
    get_stream(key, file_obj)
    return file_obj.getvalue()


@retry(tries=3, delay=5)
def get_stream(key: str, stream_to: BinaryIO):
    """Get value from S3 into the given binary stream

    See TODO in `set`.
    """
    s3_client = boto3.client("s3")

    try:
        s3_client.download_fileobj(_get_bucket(), key, stream_to)
    except botocore.exceptions.ClientError as e:
        # Standardizing "Not found" errors across storage backends
        if "404" in str(e):
            raise KeyError("{}: {}".format(key, str(e)))

        raise e


@retry(tries=3, delay=5)
def get_child_paths(key_prefix: str) -> List[str]:
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
    s3_client = boto3.client("s3")
    keys = []
    has_more = True
    continuation_token = None
    while has_more:
        list_objects_return = s3_client.list_objects_v2(
            _get_bucket(), Prefix=key_prefix, ContinuationToken=continuation_token
        )
        has_more = list_objects_return["IsTruncated"]
        continuation_token = list_objects_return.get("NextContinuationToken")
        for obj in list_objects_return["Contents"]:
            keys.append(obj["Key"])
    return keys
