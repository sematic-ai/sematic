# Standard library
from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass
class Link:
    label: str
    url: str

    def __init__(self, label: str, url: str):
        parsed_url = urlparse(url)
        if len(parsed_url.scheme) == 0 or len(parsed_url.netloc) == 0:
            raise ValueError("Incorrect URL: {}".format(repr(parsed_url)))

        self.label = label
        self.url = url
