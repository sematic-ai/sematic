# Standard Library
from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass
class Link:
    """
    Link lets users return a URL from a Sematic function which
    will render as a button in the UI.

    Parameters
    ----------
    label: str
        The label of the button that will be displayed in the UI
    url: str
        The URL to link to

    Raises
    ------
    ValueError
        In case of missing URL scheme and netloc as extracted by `urllib.parse.urlparse`.
    """

    label: str
    url: str

    def __init__(self, label: str, url: str):
        parsed_url = urlparse(url)

        if len(parsed_url.scheme) == 0:
            raise ValueError(
                f"Incorrect URL, missing scheme (e.g. https://): {repr(parsed_url)}"
            )

        if len(parsed_url.netloc) == 0:
            raise ValueError(
                f"Incorrect URL, missing netloc (e.g. https://<netloc>): {repr(parsed_url)}"  # noqa: E501
            )

        self.label = label
        self.url = url
