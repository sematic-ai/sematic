# Standard Library
from typing import Any, Dict, cast

# Third-party
import flask.testing

# Sematic
import sematic.api.endpoints.meta  # noqa: F401
from sematic.api.app import sematic_api  # noqa: F401
from sematic.api.tests.fixtures import (  # noqa: F401
    mock_requests,
    mock_user_settings,
    test_client,
)
from sematic.config.user_settings import UserSettingsVar
from sematic.db.tests.fixtures import persisted_user, test_db  # noqa: F401
from sematic.versions import CURRENT_VERSION, MIN_CLIENT_SERVER_SUPPORTS


def test_env(test_client: flask.testing.FlaskClient):  # noqa: F811
    with mock_user_settings(
        {
            UserSettingsVar.GRAFANA_PANEL_URL: "abc",
            UserSettingsVar.SEMATIC_AUTHENTICATE: "false",
        }
    ):
        response = test_client.get("/api/v1/meta/env")
        payload = response.json
        payload = cast(Dict[str, Any], payload)

        assert payload["env"][UserSettingsVar.GRAFANA_PANEL_URL.value] == "abc"


def test_versions(test_client: flask.testing.FlaskClient):  # noqa: F811
    response = test_client.get("/api/v1/meta/versions")
    payload = response.json
    payload = cast(Dict[str, Any], payload)

    assert tuple(payload["server"]) == CURRENT_VERSION
    assert tuple(payload["min_client_supported"]) == MIN_CLIENT_SERVER_SUPPORTS
