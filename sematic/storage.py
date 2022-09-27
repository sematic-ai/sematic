# Standard Library
import io

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


@retry(tries=3, delay=5)
def get(key: str) -> bytes:
    """Get value from S3.

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
