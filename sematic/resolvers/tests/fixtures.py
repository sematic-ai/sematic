# Standard Library
from unittest import mock

# Third-party
import pytest

# Sematic
from sematic.tests.fixtures import MockStorage


@pytest.fixture
def mock_local_resolver_storage():
    mock_storage = MockStorage()
    with mock.patch(
        "sematic.resolvers.local_resolver.LocalStorage", return_value=mock_storage
    ):
        yield mock_storage


@pytest.fixture
def mock_cloud_resolver_storage():
    mock_storage = MockStorage()
    with mock.patch(
        "sematic.resolvers.cloud_resolver.S3Storage", return_value=mock_storage
    ):
        yield mock_storage
