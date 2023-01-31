# Standard Library
import contextlib
import os
from typing import Dict, Optional

# Third-party
import pytest

# Sematic
import sematic.api_client as api_client
import sematic.config.settings as sematic_settings
from sematic.plugins.storage.memory_storage import MemoryStorage


class MockStorage(MemoryStorage):
    def set_from_file(self, key, file_path):
        with open(file_path, "rb") as fp:
            self._store[key] = b"".join(fp)

    def get_line_stream(self, key):
        as_bytes = self.get(key)
        as_str = str(as_bytes, encoding="utf8")
        for line in as_str.split("\n"):
            yield line

    def get_child_paths(self, key_prefix):
        if not key_prefix.endswith("/"):
            key_prefix = f"{key_prefix}/"
        return [key for key in self._store.keys() if key.startswith(key_prefix)]


@pytest.fixture(scope="function")
def test_storage():
    yield MockStorage


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
        # in case the specified variables are settings overrides, we need to
        # force reloading of global settings in order to apply the overrides
        sematic_settings._ACTIVE_SETTINGS = None

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
