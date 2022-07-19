# Standard library
import io

# Third-party
import boto3
import botocore.exceptions

# Sematic
from sematic.user_settings import get_user_settings, SettingsVar


def _get_bucket() -> str:
    return get_user_settings(SettingsVar.AWS_S3_BUCKET)


def set(key: str, value: bytes):
    """
    Store value in S3

    TODO: modularize the F out of this to enable local/remote storage switch
    based on resolver. Also enable multiple storage clients (AWS, GCP, Azure)
    """
    s3_client = boto3.client("s3")

    with io.BytesIO(value) as file_obj:
        s3_client.upload_fileobj(file_obj, _get_bucket(), key)


def get(key: str) -> bytes:
    """
    Get value from S3.

    See TODO in `set`.
    """
    s3_client = boto3.client("s3")

    file_obj = io.BytesIO()

    try:
        s3_client.download_fileobj(_get_bucket(), key, file_obj)
    except botocore.exceptions.ClientError as e:
        # Standardizing "Not found" errors across storage backends
        if "404" in str(e):
            raise KeyError("{}: {}".format(key, str(e)))

        raise e

    return file_obj.getvalue()
