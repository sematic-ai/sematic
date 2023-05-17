"""
The GitHub Publisher plugin implementation.
"""
# Standard Library
import logging
from typing import Any, Type, cast

# Sematic
# Required so that the endpoint will get registered when this plugin is used & imported.
import sematic.ee.plugins.publishing.github.endpoints  # noqa: F401
from sematic.abstract_plugin import (
    SEMATIC_PLUGIN_AUTHOR,
    AbstractPlugin,
    AbstractPluginSettingsVar,
    PluginVersion,
)
from sematic.db.models.resolution import Resolution
from sematic.ee.plugins.publishing.github.check import GitHubPublisherSettingsVar
from sematic.plugins.abstract_publisher import AbstractPublisher

logger = logging.getLogger(__name__)

_PLUGIN_VERSION = (0, 1, 0)


class GitHubPublisher(AbstractPublisher, AbstractPlugin):
    @staticmethod
    def get_author() -> str:
        return SEMATIC_PLUGIN_AUTHOR

    @staticmethod
    def get_version() -> PluginVersion:
        return _PLUGIN_VERSION

    @classmethod
    def get_settings_vars(cls) -> Type[AbstractPluginSettingsVar]:
        return GitHubPublisherSettingsVar

    def publish(self, event: Any) -> None:
        """Check a GitHub commit and update GitHub if necessary"""
        if not isinstance(event, Resolution):
            logger.debug("The received event is not a resolution event")
            return

        resolution = cast(Resolution, event)
        logger.warning("Not implemented! %s", resolution)
