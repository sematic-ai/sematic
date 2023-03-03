# Standard Library
import tempfile
from typing import IO

# Third-party
import pytest

# Sematic
from sematic.types.serialization import get_json_encodable_summary
from sematic.types.types.image import Image


@pytest.fixture(scope="function")
def temp_file():
    with tempfile.NamedTemporaryFile() as file:
        bytes_ = b"foobar"
        file.write(bytes_)
        file.flush()
        file.seek(0)
        yield file


def test_from_file(temp_file: IO[bytes]):
    image = Image.from_file(temp_file.name)
    assert image.bytes == temp_file.read()


def test_summary(temp_file: IO[bytes]):
    image = Image.from_file(temp_file.name)

    summary, blobs = get_json_encodable_summary(image, Image)

    assert summary["mime_type"] == "text/plain"
    assert summary["bytes"]["blob"] in blobs

    assert blobs[summary["bytes"]["blob"]] == temp_file.read()
