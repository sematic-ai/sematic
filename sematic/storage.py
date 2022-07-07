# Standard library
import io

# Third-party
import boto3

# Sematic
from sematic.user_settings import get_user_settings, SettingsVar


def _get_bucket() -> str:
    bucket_name = get_user_settings(SettingsVar.AWS_S3_BUCKET)

    s3 = boto3.client("s3")
    response = s3.list_buckets()

    for bucket in response["Buckets"]:
        if bucket["Name"] == bucket_name:
            return bucket_name

    raise ValueError(
        "No such bucket: {}, are you sure it was created?".format(repr(bucket_name))
    )


def set(key: str, value: str):
    """
    Store value in S3

    TODO: modularize the F out of this to enable local/remote storage switch
    based on resolver. Also enable multiple storage clients (AWS, GCP, Azure)
    """
    s3_client = boto3.client("s3")

    bucket = _get_bucket()

    with io.StringIO(value) as file_obj:
        s3_client.upload_file(key, bucket, file_obj)


def get(key: str) -> str:
    """
    Get value from S3.

    See TODO in `set`.
    """
    bucket = _get_bucket()

    s3_client = boto3.client("s3")

    with io.StringIO() as file_obj:
        s3_client.download_fileobj(bucket, key, file_obj)

        return file_obj.read()
