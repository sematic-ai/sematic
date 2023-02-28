# Standard Library
import sys

# Third-party
# confirm that third party dependencies were installed
import requests  # noqa: F401


def test_py3_8():
    assert sys.version_info[0:2] == (3, 8)
