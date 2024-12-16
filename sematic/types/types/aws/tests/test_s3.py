# Third-party
import pytest

# Sematic
from sematic.types.types.aws.s3 import S3Bucket, S3Location


@pytest.mark.parametrize(
    "uri, error_message",
    (
        (
            "https://s3.console.aws.amazon.com/s3/object/example/file",
            "Malformed S3 URI. Must start with s3://",
        ),
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
        ("s3://foo/bar/bat/", "foo", None, "bar/bat/"),
        ("s3://foo/bar/bat", "foo", "us-west-2", "bar/bat"),
        ("s3://foo/bar/bat/", "foo", "us-west-2", "bar/bat/"),
    ),
)
def test_from_uri(uri, bucket_name, region, location):
    s3_location = S3Location.from_uri(uri, region=region)

    assert s3_location.bucket.name == bucket_name
    assert s3_location.bucket.region == region
    assert s3_location.location == location


@pytest.mark.parametrize(
    "current_location, parent_directory", (("foo/bar", "foo/"), ("foo/bar/", "foo/"))
)
def test_parent_directory(current_location, parent_directory):
    location = S3Location(
        bucket=S3Bucket(name="bucket"),
        location=current_location,
    )

    parent_location = location.parent_directory

    assert parent_location.bucket == location.bucket
    assert parent_location.location == parent_directory


@pytest.mark.parametrize(
    "current_location, sibling_file_location, sibling_dir_location",
    (("foo/bar", "foo/bat", "foo/bat/"), ("foo/bar/", "foo/bat", "foo/bat/")),
)
def test_sibling_location(current_location, sibling_file_location, sibling_dir_location):
    location = S3Location(
        bucket=S3Bucket(name="bucket"),
        location=current_location,
    )

    sibling = location.sibling_location("bat")

    assert sibling.bucket == location.bucket
    assert sibling.location == sibling_file_location

    sibling = location.sibling_location("bat/")

    assert sibling.bucket == location.bucket
    assert sibling.location == sibling_dir_location


@pytest.mark.parametrize(
    "current_location, child_file_location, child_dir_location",
    (
        ("foo/bar", "foo/bar/bat", "foo/bar/bat/"),
        ("foo/bar/", "foo/bar/bat", "foo/bar/bat/"),
    ),
)
def test_child_location(current_location, child_file_location, child_dir_location):
    location = S3Location(
        bucket=S3Bucket(name="bucket"),
        location=current_location,
    )

    sibling = location.child_location("bat")

    assert sibling.bucket == location.bucket
    assert sibling.location == child_file_location

    sibling = location.child_location("bat/")

    assert sibling.bucket == location.bucket
    assert sibling.location == child_dir_location


@pytest.mark.parametrize(
    "current_location, sibling_file_location, sibling_dir_location",
    (
        ("foo/bar", "foo/bar/bat", "foo/bar/bat/"),
        ("foo/bar/", "foo/bar/bat", "foo/bar/bat/"),
    ),
)
def test_div(current_location, sibling_file_location, sibling_dir_location):
    location = S3Location(
        bucket=S3Bucket(name="bucket"),
        location=current_location,
    )

    sibling = location / "bat"

    assert sibling.bucket == location.bucket
    assert sibling.location == sibling_file_location

    sibling = location / "bat/"

    assert sibling.bucket == location.bucket
    assert sibling.location == sibling_dir_location


def test_to_uri():
    assert (
        S3Location(bucket=S3Bucket(name="foo"), location="bar/bat").to_uri()
        == "s3://foo/bar/bat"
    )
    assert (
        S3Location(bucket=S3Bucket(name="foo"), location="bar/bat/").to_uri()
        == "s3://foo/bar/bat/"
    )
