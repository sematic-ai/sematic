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
from sematic.db.models.resolution import Resolution, ResolutionStatus
from sematic.db.queries import get_run
from sematic.ee.plugins.publishing.github.check import (
    COMMIT_CHECK_PREFIX,
    GitHubPublisherSettingsVar,
    check_commit,
)
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
        if not ResolutionStatus[resolution.status].is_terminal():  # type: ignore
            logger.debug("The received event is not a resolution termination")
            return

        run = get_run(resolution.root_id)
        is_part_of_check = any(
            tag.startswith(COMMIT_CHECK_PREFIX) for tag in run.tag_list
        )
        if is_part_of_check:
            if resolution.git_info is None:
                logger.error(
                    "Not updating GitHub for resolution %s because it has no GitInfo.",
                    resolution.root_id,
                )
                return
            check_commit(resolution.git_info)
