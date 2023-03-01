# Third-party
import pytest

# Sematic
from sematic.types.types.aws.s3 import S3Location


@pytest.mark.parametrize(
    "uri, error_message",
    (
        ("", "Malformed S3 URI. Must start with s3://"),
        ("s3://", "URI is missing a bucket"),
        ("s3://foo", "URI is missing a path"),
        ("s3://foo/", "URI is missing a path"),
    ),
)
def test_from_uri_fail(uri, error_message):
    with pytest.raises(ValueError, match=error_message):
        S3Location.from_uri(uri)


@pytest.mark.parametrize(
    "uri, bucket_name, region, location",
    (
        ("s3://foo/bar/bat", "foo", None, "bar/bat"),
        ("s3://foo/bar/bat", "foo", "us-west-2", "bar/bat"),
    ),
)
def test_from_uri(uri, bucket_name, region, location):
    s3_location = S3Location.from_uri(uri, region=region)

    assert s3_location.bucket.name == bucket_name
    assert s3_location.bucket.region == region
    assert s3_location.location == location
