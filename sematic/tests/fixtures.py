# Standard Library
import contextlib
import os
from typing import Dict, Optional

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


@contextlib.contextmanager
def environment_variables(to_set: Dict[str, Optional[str]]):
    """Context manager to configure the os environ for tests.

    Parameters
    ----------
    to_set:
        A dict from env var name to env var value. If the env var value
        is None, that will be treated as indicating that the env var should
        be unset within the managed context.
    """
    backup_of_changed_keys = {k: os.environ.get(k, None) for k in to_set.keys()}

    def update_environ_with(env_dict):
        for key, value in env_dict.items():
            if value is None:
                if key in os.environ:
                    del os.environ[key]
            else:
                os.environ[key] = value

    update_environ_with(to_set)
    try:
        yield
    finally:
        update_environ_with(backup_of_changed_keys)
