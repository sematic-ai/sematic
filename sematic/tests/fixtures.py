# Third-party
import pytest

# Sematic
import sematic.api_client as api_client
import sematic.storage as storage


@pytest.fixture(scope="function")
def test_storage():
    current_set = storage.set
    current_get = storage.get

    store = {}

    def _set(key, value):
        store[key] = value

    def _get(key):
        return store[key]

    storage.set = _set
    storage.get = _get

    try:
        yield
    finally:
        storage.set = current_set
        storage.get = current_get


@pytest.fixture
def valid_client_version():
    current_validated_client_version = api_client._validated_client_version

    api_client._validated_client_version = True

    try:
        yield
    finally:
        api_client._validated_client_version = current_validated_client_version
