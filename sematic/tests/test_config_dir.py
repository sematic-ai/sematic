# Standard Library
import pathlib

# Third-party
import pytest

# Sematic
from sematic.config_dir import _CONFIG_DIR_OVERRIDE_ENV_VAR, get_config_dir
from sematic.tests.fixtures import environment_variables


def test_get_config_dir_default():
    with environment_variables({_CONFIG_DIR_OVERRIDE_ENV_VAR: None}):
        config_dir = get_config_dir()
        assert pathlib.Path(config_dir).is_absolute()
        assert pathlib.Path.home().as_posix() in config_dir
        assert pathlib.Path(config_dir).as_posix().endswith("/.sematic")


def test_get_config_override():
    with environment_variables({_CONFIG_DIR_OVERRIDE_ENV_VAR: ".foo"}):
        config_dir = get_config_dir()
        assert pathlib.Path(config_dir).is_absolute()
        assert pathlib.Path.home().as_posix() in config_dir
        assert pathlib.Path(config_dir).as_posix().endswith("/.foo")


def test_get_config_override_absolute():
    with environment_variables({_CONFIG_DIR_OVERRIDE_ENV_VAR: "/tmp/.foo"}):
        config_dir = get_config_dir()
        assert pathlib.Path(config_dir).as_posix() == "/tmp/.foo"


def test_get_config_override_bad_parent():
    with environment_variables(
        {_CONFIG_DIR_OVERRIDE_ENV_VAR: "/this-doesnt-exist/.foo"}
    ):
        with pytest.raises(ValueError, match=r"this-doesnt-exist"):
            get_config_dir()
