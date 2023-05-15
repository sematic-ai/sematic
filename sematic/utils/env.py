# Standard Library
import contextlib
import os
from typing import Dict, Optional

# Sematic
import sematic.config.settings as sematic_settings


@contextlib.contextmanager
def environment_variables(to_set: Dict[str, Optional[str]]):
    """
    Context manager to configure the os environ.

    After exiting the context, the original env vars will be back in place.

    Parameters
    ----------
    to_set:
        A dict from env var name to env var value. If the env var value is None, that will
        be treated as indicating that the env var should be unset within the managed
        context.
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
