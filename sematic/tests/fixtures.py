# Third-party
import pytest

# Sematic
import sematic.storage as storage


@pytest.fixture(scope="function")
def test_storage():
    current_set = storage.set
    current_get = storage.get

    storage.set = lambda _, __: None
    storage.get = lambda _: _

    try:
        yield
    finally:
        storage.set = current_set
        storage.get = current_get
