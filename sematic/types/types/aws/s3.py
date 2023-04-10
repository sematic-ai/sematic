# Standard Library
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlsplit


@dataclass
class S3Bucket:
    """
    Basic type to describe an S3 bucket.
    """

    name: str
    region: Optional[str] = None


@dataclass
class S3Location:
    """
    Basic type to describe an S3 location.

    S3 only emulates a file system through key-value pairs and does not have an actual
    hierarchical directory structure. As a convention, locations that end in a "/" are
    rendered as "directories", and those that do not are interpreted as fully-qualified
    file paths.
    """

    bucket: S3Bucket
    location: str

    @classmethod
    def from_uri(cls, uri: str, region: Optional[str] = None) -> "S3Location":
        """
        Construct an S3Location object from an S3 URI of the form
        `s3://bucket-name/path/to/location`.

        Parameters
        ----------
        uri: str
            S3 URI
        region: Optional[str]
            S3 bucket's region
        """
        split_uri = urlsplit(uri)

        if split_uri.scheme != "s3":
            raise ValueError(f"Malformed S3 URI. Must start with s3://: {uri}")

        if len(split_uri.netloc) == 0:
            raise ValueError(f"URI is missing a bucket: {uri}")

        location = split_uri.path

        if len(location) > 0 and location[0] == "/":
            location = location[1:]

        if len(location) == 0:
            raise ValueError(f"URI is missing a path: {uri}")

        return S3Location(
            bucket=S3Bucket(name=split_uri.netloc, region=region), location=location
        )

    def to_uri(self) -> str:
        return f"s3://{self.bucket.name}/{self.location}"

    @property
    def parent_directory(self) -> "S3Location":
        """
        The S3Location of the parent directory.

        If current location is a file, the parent directory is the directory in
        which the file is stored. If the current location is a directory, the
        parent directory is its parent directory.

        Returns
        -------
        S3Location
        """
        location = self.location[:-1] if self.location[-1] == "/" else self.location
        location_parts = location.split("/")
        parent_location = f"{'/'.join(location_parts[:-1])}/"

        return S3Location(bucket=self.bucket, location=parent_location)

    def sibling_location(self, location: str) -> "S3Location":
        """
        A location in the same parent directory as the current location.

        Returns
        -------
        S3Location
        """
        return S3Location(
            bucket=self.bucket,
            location=f"{self.parent_directory.location}{location}",
        )

    def child_location(self, location: str) -> "S3Location":
        """
        A location under the current location.

        Returns
        -------
        S3Location
        """
        child_location = self.location
        if not child_location.endswith("/"):
            child_location = child_location + "/"

        return S3Location(bucket=self.bucket, location=f"{child_location}{location}")

    def __truediv__(self, location: str) -> "S3Location":
        return self.child_location(location)
