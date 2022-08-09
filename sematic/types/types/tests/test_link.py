# Sematic
from sematic.types.types.link import Link

# Third-party
import pytest


def test_url_validation_pass():
    link = Link(label="my link", url="https://example.com")
    assert link.label == "my link"
    assert link.url == "https://example.com"


@pytest.mark.parametrize(
    "expected_exception_str, url",
    (
        ("Incorrect URL, missing scheme", "foo"),
        ("Incorrect URL, missing netloc", "foo://"),
    ),
)
def test_url_validation_fail(expected_exception_str, url):
    with pytest.raises(ValueError, match=expected_exception_str):
        Link(label="my link", url=url)
