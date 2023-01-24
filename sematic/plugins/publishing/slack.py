# Standard Library
import logging
from typing import Type

# Third-party
import requests

# Sematic
from sematic.abstract_plugin import (
    AbstractPlugin,
    AbstractPluginSettingsVar,
    PluginVersion,
)
from sematic.config.settings import get_plugin_setting
from sematic.db.models.resolution import Resolution, ResolutionStatus
from sematic.db.queries import get_run
from sematic.plugins.abstract_publisher import AbstractPublisher
from sematic.utils.memoized_property import memoized_property

logger = logging.getLogger(__name__)

_PLUGIN_VERSION = (0, 1, 0)
_SLACK_HEADERS = {"Content-Type": "application/json"}
_SLACK_URL_TEMPLATE = "https://hooks.slack.com/services/{webhook_token}"
# TODO: implement server-side gnostic components that build urls that point to specific
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
    SLACK_EXTERNAL_URL = "SLACK_EXTERNAL_URL"


class SlackPublisher(AbstractPublisher, AbstractPlugin):
    @staticmethod
    def get_author() -> str:
        return "github.com/sematic-ai"

    @staticmethod
    def get_version() -> PluginVersion:
        return _PLUGIN_VERSION

    @classmethod
    def get_settings_vars(cls) -> Type[AbstractPluginSettingsVar]:
        return SlackPublisherSettingsVar

    @memoized_property
    def _slack_url(self) -> str:
        webhook_token = get_plugin_setting(
            self.__class__, SlackPublisherSettingsVar.SLACK_WEBHOOK_TOKEN
        )
        return _SLACK_URL_TEMPLATE.format(webhook_token=webhook_token)

    def _get_message(self, resolution: Resolution) -> str:
        """
        Returns the message to publish.
        """
        external_url = get_plugin_setting(
            self.__class__, SlackPublisherSettingsVar.SLACK_EXTERNAL_URL
        )
        # TODO: in the future we might either have a gnostic server-side component build
        #  this url for us (e.g. have resolutions.py build a path to the specific
        #  resolution panel), or have a url which only contains the resolution root id
        #  redirect to the full url path
        root_run = get_run(run_id=resolution.root_id)

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

    def publish(self, resolution: Resolution) -> None:
        """
        Publishes a message to the configured Slack channel in case the Resolution failed.
        """
        # we are currently publishing only on failure events
        if resolution.status != ResolutionStatus.FAILED.value:
            logger.debug("Not publishing resolution")
            return

        try:
            json_data = {"text": self._get_message(resolution=resolution)}
            kwargs = dict(headers=_SLACK_HEADERS)

            logger.debug(
                "Publishing resolution failure to Slack: url=`%s` json=`%s` kwargs=`%s`",
                self._slack_url,
                json_data,
                kwargs,
            )
            requests.post(url=self._slack_url, json=json_data, **kwargs)  # type: ignore
            logger.info("Published resolution failure to Slack")

        except Exception:
            logger.exception(
                "Unable to publish the resolution failure message to Slack"
            )
