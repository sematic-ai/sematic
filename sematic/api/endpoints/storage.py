# Standard Library
from dataclasses import dataclass

# Sematic
from sematic.config.user_settings import UserSettingsVar, get_user_settings
from sematic.storage import StorageMode, StorageSettingValue, get_storage


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

    storage_setting_value = get_user_settings(
        UserSettingsVar.SEMATIC_STORAGE, StorageSettingValue.LOCAL.value
    ).upper()

    try:
        storage_engine_class = get_storage(StorageSettingValue[storage_setting_value])
    except KeyError:
        raise UnknownStorageEngineError(
            f"Unknown storage engine: {storage_setting_value}"
        )

    location = storage_engine_class().get_location(
        namespace=namespace, key=object_id, mode=storage_mode
    )

    return StorageLocationPayload(storage_engine=storage_setting_value, location=location)
