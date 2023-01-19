# Standard Library
from typing import Type, cast

# Sematic
from sematic.abstract_plugin import PluginScope
from sematic.config.settings import get_active_plugins
from sematic.plugins.abstract_storage import AbstractStorage
from sematic.plugins.storage.local_storage import LocalStorage


class NoActivePluginError(Exception):
    pass


def get_storage_plugin() -> Type[AbstractStorage]:
    try:
        storage_plugin = get_active_plugins(
            PluginScope.STORAGE, default=[LocalStorage]
        )[0]
    except IndexError:
        raise NoActivePluginError()

    storage_class = cast(Type[AbstractStorage], storage_plugin)

    return storage_class
