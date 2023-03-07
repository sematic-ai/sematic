# Standard Library
import logging
from typing import Any
from unittest import mock

# Third-party
import pytest

# Sematic
from sematic.config.server_settings import ServerSettingsVar
from sematic.config.tests.fixtures import mock_settings
from sematic.db.models.resolution import Resolution, ResolutionStatus
from sematic.db.models.run import Run
from sematic.db.tests.fixtures import (  # noqa: F401
    allow_any_run_state_transition,
    make_resolution,
    persisted_resolution,
    persisted_run,
    run,
    test_db,
)
from sematic.plugins.publishing.slack import SlackPublisher, SlackPublisherSettingsVar
from sematic.tests.fixtures import environment_variables
from sematic.tests.utils import assert_logs_captured

_TEST_ENV_VARS = {
    ServerSettingsVar.SEMATIC_DASHBOARD_URL.value: "https://my.sematic",
    SlackPublisherSettingsVar.SLACK_WEBHOOK_TOKEN.value: "XX/YY/ZZ",
}


# auto-mocking the requests.post function for all tests in order to protect against
# incorrect tests actually making calls to the slack service
@pytest.fixture(scope="function", autouse=True)
def mock_post():
    with mock.patch("requests.post") as mock_post_:
        yield mock_post_


@pytest.fixture
def failed_resolution() -> Resolution:
    return make_resolution(status=ResolutionStatus.FAILED)


def test_publish_happy(
    mock_post: mock.MagicMock,
    persisted_run: Run,  # noqa: F811
):
    id = persisted_run.id
    resolution = make_resolution(  # noqa: F811
        root_id=id, status=ResolutionStatus.FAILED
    )

    expected_message = (
        f":red_circle: test_run run "
        f"<https://my.sematic/pipelines/path.to.test_run/{id}#tab=logs|{id[0:6]}> "
        f"has failed."
    )

    with mock_settings(None):
        with environment_variables(_TEST_ENV_VARS):  # type: ignore
            slack_publisher = SlackPublisher()
            slack_publisher.publish(event=resolution)

            mock_post.assert_called_with(
                url="https://hooks.slack.com/services/XX/YY/ZZ",
                json={"text": expected_message},
                headers={"Content-Type": "application/json"},
            )


def test_non_resolution_event(mock_post: mock.MagicMock, caplog):
    with mock_settings(None):
        with environment_variables(_TEST_ENV_VARS):  # type: ignore
            with caplog.at_level(logging.DEBUG):
                slack_publisher = SlackPublisher()
                slack_publisher.publish(event="this is a string, not a Resolution")

                mock_post.assert_not_called()
                assert_logs_captured(
                    caplog, "The received event is not a resolution event"
                )


def test_non_failed_resolution(
    mock_post: mock.MagicMock,
    persisted_resolution: Resolution,  # noqa: F811
    caplog: Any,
):
    with mock_settings(None):
        with environment_variables(_TEST_ENV_VARS):  # type: ignore
            with caplog.at_level(logging.DEBUG):
                slack_publisher = SlackPublisher()
                slack_publisher.publish(event=persisted_resolution)

                mock_post.assert_not_called()
                assert_logs_captured(
                    caplog, "The received resolution event is not a failure"
                )


def test_missing_dashboard_url(
    mock_post: mock.MagicMock,
    failed_resolution: Resolution,  # noqa: F811
    caplog: Any,
):
    with mock_settings(None):
        with environment_variables(  # type: ignore
            {SlackPublisherSettingsVar.SLACK_WEBHOOK_TOKEN.value: "XX/YY/ZZ"}
        ):
            with caplog.at_level(logging.DEBUG):
                slack_publisher = SlackPublisher()
                slack_publisher.publish(event=failed_resolution)

                mock_post.assert_not_called()
                assert_logs_captured(
                    caplog, "Unable to publish the resolution failure message to Slack"
                )


def test_missing_webhook_token(
    mock_post: mock.MagicMock,
    failed_resolution: Resolution,  # noqa: F811
    caplog: Any,
):
    with mock_settings(None):
        with environment_variables(  # type: ignore
            {ServerSettingsVar.SEMATIC_DASHBOARD_URL.value: "https://my.sematic"}
        ):
            with caplog.at_level(logging.DEBUG):
                slack_publisher = SlackPublisher()
                slack_publisher.publish(event=failed_resolution)

                mock_post.assert_not_called()
                assert_logs_captured(
                    caplog, "Unable to publish the resolution failure message to Slack"
                )


def test_malformed_webhook_token(
    mock_post: mock.MagicMock,
    failed_resolution: Resolution,  # noqa: F811
    caplog: Any,
):
    with mock_settings(None):
        with environment_variables(  # type: ignore
            {
                ServerSettingsVar.SEMATIC_DASHBOARD_URL.value: "https://my.sematic",
                SlackPublisherSettingsVar.SLACK_WEBHOOK_TOKEN.value: "bad token",
            }
        ):
            with caplog.at_level(logging.DEBUG):
                slack_publisher = SlackPublisher()
                slack_publisher.publish(event=failed_resolution)

                mock_post.assert_not_called()
                assert_logs_captured(
                    caplog, "Unable to publish the resolution failure message to Slack"
                )
