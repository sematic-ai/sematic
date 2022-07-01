# Standard library
import tempfile
from unittest.mock import patch, PropertyMock

# Third-party
import pytest
import yaml

# Sematic
import sematic.credentials
from sematic.credentials import get_credentials


@pytest.fixture(scope="function")
def credentials_file():
    with tempfile.NamedTemporaryFile() as tf:
        with patch(
            "sematic.config.Config.credentials_file",
            return_value=tf.name,
            new_callable=PropertyMock,
        ):
            current_credentials = sematic.credentials._credentials
            sematic.credentials._credentials = None

            yield tf

            sematic.credentials._credentials = current_credentials


def test_get_empty_credentials(credentials_file):
    assert get_credentials() == {}


def test_get_credentials(credentials_file):
    credentials = {"default": {"snowflake": {"SNOWFLAKE_USER": "foobar"}}}
    yaml_output = yaml.dump(credentials, Dumper=yaml.Dumper)
    credentials_file.write(bytes(yaml_output, encoding="utf-8"))
    credentials_file.flush()
    assert get_credentials() == credentials["default"]
