"""
The module that contains the definition of the AbstractBuilder plugin, which packages user
code and builds container images that can be used to execute the user's funcs.
"""

# Standard Library
import abc
import os
from typing import Optional, Type, cast

# Sematic
from sematic.abstract_plugin import AbstractPlugin, PluginScope
from sematic.config.settings import get_active_plugins


RUN_COMMAND_ENV_VAR = "SEMATIC_CLI_RUN_COMMAND"
BUILD_CONFIG_ENV_VAR = "SEMATIC_IMAGE_BUILD_CONFIG"


class BuildError(Exception):
    """
    A pipeline build execution failed.
    """

    pass


class BuildConfigurationError(BuildError):
    """
    A pipeline build configuration is invalid.
    """

    pass


class AbstractBuilder(AbstractPlugin):
    """
    Abstract base class to represent a container image builder and launcher.
    """

    def __init__(self, **_):
        super().__init__()

    @abc.abstractmethod
    def build_and_launch(self, target: str, run_command: Optional[str]) -> None:
        """
        Builds a container image and launches the specified target launch script.

        Parameters
        ----------
        target: str
            The path to the pipeline target to launch; the built image must support this
            target's execution.
        run_command: Optional[str]
            The CLI command used to launch the pipeline, if applicable.
        """

        pass


def get_builder_plugin(default: Type[AbstractPlugin]) -> Type[AbstractBuilder]:
    """
    Return the configured "BUILD" scope plugin type, or the specified default plugin type.
    """
    builder_plugins = get_active_plugins(scope=PluginScope.BUILD, default=[default])

    if len(builder_plugins) > 1:
        raise ValueError(
            "Only one plugin can be configured for the %s scope; found: %s",
            PluginScope.BUILD.value,
            builder_plugins,
        )

    builder_class = cast(Type[AbstractBuilder], builder_plugins[0])
    return builder_class


def get_run_command() -> Optional[str]:
    """
    Returns the CLI command used to launch the currently-executing pipeline, if any.
    """
    return os.environ.get(RUN_COMMAND_ENV_VAR)


def get_build_config() -> Optional[str]:
    """
    Returns the configuration used to build the currently-executing pipeline container
    image, if any.
    """
    return os.environ.get(BUILD_CONFIG_ENV_VAR)
