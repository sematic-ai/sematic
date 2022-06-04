# Standard library
from dataclasses import dataclass
from enum import Enum
import os
import pathlib
from urllib.parse import urljoin


_DEFAULT_CONFIG_DIR = ".glow"


def _get_config_dir() -> str:
    home_dir = pathlib.Path.home()
    config_dir = os.path.join(home_dir, _DEFAULT_CONFIG_DIR)
    try:
        os.mkdir(config_dir)
    except FileExistsError:
        pass

    return config_dir


@dataclass
class Config:
    api_server_url: str
    api_version: int
    config_dir: str = _get_config_dir()

    @property
    def api_url(self):
        return urljoin(self.api_server_url, "api/v{}".format(self.api_version))


_LOCAL_CONFIG = Config(api_server_url="http://127.0.0.1:5000", api_version=1)


class StandardConfigs(Enum):
    local = _LOCAL_CONFIG


DEFAULT_ENV = "local"


_active_config = StandardConfigs[DEFAULT_ENV].value


def get_config() -> Config:
    global _active_config
    return _active_config
