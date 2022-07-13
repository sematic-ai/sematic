# Third-party
import pytest

# Sematic
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
