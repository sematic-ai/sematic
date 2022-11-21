# Standard Library
import distutils.util
import enum
import logging
from typing import Any, Dict, Optional, Union

# Third-party
import yaml

logger = logging.getLogger(__name__)

EnumType = type(enum.Enum)
SettingsType = Dict[EnumType, str]  # type: ignore


class EnumDumper(yaml.Dumper):
    """
    Custom Dumper for Enum values.

    It serializes Enums as simple strings so that the values aren't represented as class
    instances with type metadata.

    It also deactivates aliases, avoiding creating referential ids in the resulting yaml
    contents.
    """

    def __init__(self, stream, **kwargs):
        super(EnumDumper, self).__init__(stream, **kwargs)
        self.add_multi_representer(
            enum.Enum, lambda _, var: self.represent_str(str(var.value))
        )

    def ignore_aliases(self, data: Any) -> bool:
        return True


def _as_bool(value: Optional[Any]) -> bool:
    """
    Returns a boolean interpretation of the contents of the specified value.
    """
    if isinstance(value, bool):
        return value

    if value is None:
        return False

    str_value = str(value)
    if len(str_value) == 0:
        return False

    return bool(distutils.util.strtobool(str_value))


def _normalize_enum(enum_type: EnumType, obj: Any):  # type: ignore
    """
    Returns a value belonging to the specified enum which corresponds to the specified
    object, if possible.
    """
    if isinstance(obj, enum_type):
        return obj

    try:
        return enum_type[str(obj)]  # type: ignore
    except KeyError:
        return None


def _load_settings(file_path: str) -> Dict[str, Union[str, Dict[str, str]]]:
    """
    Loads the settings from the specified settings file, returning their raw string
    representations, or an empty dict if the file is not found.
    """
    try:
        with open(file_path, "r") as f:
            return yaml.load(f, yaml.Loader)

    except FileNotFoundError:
        logger.debug("Settings file %s not found", file_path)
        return {}


def _save_settings(file_path: str, settings: SettingsType) -> None:
    """
    Persists the specified settings to the specified settings file.
    """
    yaml_output = yaml.dump(settings, Dumper=EnumDumper)

    with open(file_path, "w") as f:
        f.write(yaml_output)


def dump_settings(settings: SettingsType) -> str:
    """
    Dumps the specified settings to string.
    """
    return yaml.dump(settings, default_flow_style=False, Dumper=EnumDumper)
