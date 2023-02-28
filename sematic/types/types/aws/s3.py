# Standard Library
from dataclasses import dataclass


@dataclass
class S3Bucket:
    region: str
    name: str


@dataclass
class S3Location:
    bucket: S3Bucket
    location: str
