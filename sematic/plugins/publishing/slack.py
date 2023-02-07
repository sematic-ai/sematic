"""
The Slack Publisher plugin implementation.
"""
# Standard Library
import logging
import re
from typing import Any, Type, cast

# Third-party
import requests

# Sematic
from sematic.abstract_plugin import (
    SEMATIC_PLUGIN_AUTHOR,
    AbstractPlugin,
    AbstractPluginSettingsVar,
    PluginVersion,
)
from sematic.config.server_settings import ServerSettingsVar, get_server_setting
from sematic.config.settings import get_plugin_setting
from sematic.db.models.resolution import Resolution, ResolutionStatus
from sematic.db.queries import get_run
from sematic.plugins.abstract_publisher import AbstractPublisher

logger = logging.getLogger(__name__)

_PLUGIN_VERSION = (0, 1, 0)
_SLACK_TOKEN_PATTERN = "[a-zA-Z0-9]+/[a-zA-Z0-9]+/[a-zA-Z0-9]+"
_SLACK_HEADERS = {"Content-Type": "application/json"}
_SLACK_URL_TEMPLATE = "https://hooks.slack.com/services/{webhook_token}"
# TODO: implement server-side dedicated components that build urls that point to specific
#  resources - e.g. have resolutions.py build this url for us
# currently, this needs to be updated here whenever the endpoints change
_RESOLUTION_URL_TEMPLATE = (
    "{external_url}/pipelines/{pipeline_import_path}/{resolution_id}#tab=logs"
)
_MESSAGE_TEMPLATE = (
    ":red_circle: {resolution_name} run "
    "<{resolution_url}|{short_resolution_id}> has failed."
)


class SlackPublisherSettingsVar(AbstractPluginSettingsVar):
    SLACK_WEBHOOK_TOKEN = "SLACK_WEBHOOK_TOKEN"


class SlackPublisher(AbstractPublisher, AbstractPlugin):
    @staticmethod
    def get_author() -> str:
        return SEMATIC_PLUGIN_AUTHOR

    @staticmethod
    def get_version() -> PluginVersion:
        return _PLUGIN_VERSION

    @classmethod
    def get_settings_vars(cls) -> Type[AbstractPluginSettingsVar]:
        return SlackPublisherSettingsVar

    def _get_slack_url(self) -> str:
        webhook_token = get_plugin_setting(
            self.__class__, SlackPublisherSettingsVar.SLACK_WEBHOOK_TOKEN
        )

        # validate that this conforms to an expected token structure
        # we want to avoid spamming the slack backend service with incorrect calls,
        # or we might get blocked
        # TODO: one of the advantages of having a long-lived plugin instance is that
        #  validation can be done on initialization, then all publication calls ignored
        #  in case this failed, instead of spamming with stack traces
        if re.match(_SLACK_TOKEN_PATTERN, webhook_token) is None:
            raise ValueError(
                f"Configured value '{webhook_token}' for setting "
                f"{SlackPublisherSettingsVar.SLACK_WEBHOOK_TOKEN.value} does not "
                f"conform to the expected token format: '{_SLACK_TOKEN_PATTERN}'"
            )

        return _SLACK_URL_TEMPLATE.format(webhook_token=webhook_token)

    def _get_message(self, resolution: Resolution) -> str:
        """
        Returns the message to publish.
        """
        external_url = get_server_setting(ServerSettingsVar.SEMATIC_DASHBOARD_URL)
        root_run = get_run(run_id=resolution.root_id)

        # TODO: in the future we might either have a url-aware server-side component build
        #  this url for us (e.g. have resolutions.py build a path to the specific
        #  resolution panel), or have a url which only contains the resolution root id
        #  redirect to the full url path
        resolution_url = _RESOLUTION_URL_TEMPLATE.format(
            external_url=external_url,
            pipeline_import_path=root_run.calculator_path,
            resolution_id=resolution.root_id,
        )

        message = _MESSAGE_TEMPLATE.format(
            resolution_name=root_run.name or root_run.calculator_path,
            resolution_url=resolution_url,
            short_resolution_id=resolution.root_id[0:6],
        )

        return message

    def publish(self, event: Any) -> None:
        """
        Publishes a message to the configured Slack channel in case the Resolution failed.
        """
        if not isinstance(event, Resolution):
            logger.debug("The received event is not a resolution event")
            return

        # we are currently publishing only on failure events
        resolution = cast(Resolution, event)
        if resolution.status != ResolutionStatus.FAILED.value:
            logger.debug("The received resolution event is not a failure")
            return

        try:
            json_data = {"text": self._get_message(resolution=resolution)}
            kwargs = dict(headers=_SLACK_HEADERS)
            slack_url = self._get_slack_url()

            logger.debug(
                "Publishing resolution failure to Slack: url=`%s` json=`%s` kwargs=`%s`",
                slack_url,
                json_data,
                kwargs,
            )
            requests.post(url=slack_url, json=json_data, **kwargs)  # type: ignore
            logger.info("Published resolution failure to Slack")

        except Exception:
            logger.exception(
                "Unable to publish the resolution failure message to Slack"
            )
