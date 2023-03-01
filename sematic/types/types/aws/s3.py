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
    """

    bucket: S3Bucket
    location: str

    @classmethod
    def from_uri(cls, uri: str, region: Optional[str] = None) -> "S3Location":
        """
        Construct an S3Location object from an S3 URI of the form
        s3://bucket-name/path/to/location

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
