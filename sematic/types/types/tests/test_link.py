# Sematic
from sematic.types.types.link import Link

# Third-party
import pytest


def test_url_validation_pass():
    link = Link(label="my link", url="https://example.com")
    assert link.label == "my link"
    assert link.url == "https://example.com"


def test_url_validation_fail():
    with pytest.raises(ValueError, match="Incorrect URL"):
        Link(label="my link", url="foo")
