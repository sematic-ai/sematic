# Standard Library
from dataclasses import dataclass
from typing import Type, cast

# Sematic
from sematic.abstract_storage import AbstractStorage, StorageMode
from sematic.plugins import PluginScope, get_selected_plugin
from sematic.storage.local_storage import LocalStorage


@dataclass
class StorageLocationPayload:
    storage_engine: str
    location: str


class UnknownStorageModeError(KeyError):
    pass


class UnknownStorageEngineError(KeyError):
    pass


def get_storage_location(
    object_id: str, mode: str, namespace: str
) -> StorageLocationPayload:
    try:
        storage_mode = StorageMode[mode.upper()]
    except KeyError:
        raise UnknownStorageModeError(
            f"Storage mode should be one of {[m.value for m in StorageMode]}, got {mode}"
        )

    try:
        storage_engine_plugin = get_selected_plugin(
            PluginScope.STORAGE, default=LocalStorage
        )
    except KeyError as e:
        raise UnknownStorageEngineError(f"Unknown storage engine: {e}")

    # Ideally this would already be done by get_selected_plugin but I couldn't
    # make it work, TypeVar typed args don't accept abstract classes
    # https://github.com/python/mypy/issues/5374
    storage_engine_class: Type[AbstractStorage] = cast(
        Type[AbstractStorage], storage_engine_plugin
    )

    location = storage_engine_class().get_location(
        namespace=namespace, key=object_id, mode=storage_mode
    )

    return StorageLocationPayload(
        storage_engine=storage_engine_class.__name__, location=location
    )
