# Standard Library
from dataclasses import dataclass


@dataclass
class S3Bucket:
    """
    Basic type to describe an S3 bucket.
    """

    region: str
    name: str


@dataclass
class S3Location:
    """
    Basic type to describe an S3 location.
    """

    bucket: S3Bucket
    location: str
