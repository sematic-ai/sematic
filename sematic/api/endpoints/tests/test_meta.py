# Standard library
from typing import Any, Dict, cast

# Third-party
import flask.testing
import flask

# Sematic
from sematic.versions import CURRENT_VERSION, MIN_CLIENT_SERVER_SUPPORTS
from sematic.api.tests.fixtures import (  # noqa: F401
    mock_no_auth,
    test_client,
    mock_requests,
    mock_user_settings,
)
from sematic.db.tests.fixtures import test_db, persisted_user  # noqa: F401
import sematic.api.endpoints.meta  # noqa: F401
from sematic.api.app import sematic_api  # noqa: F401
from sematic.user_settings import SettingsVar


def test_env(test_client: flask.testing.FlaskClient):  # noqa: F811
    with mock_user_settings(
        {SettingsVar.GRAFANA_PANEL_URL: "abc", SettingsVar.SEMATIC_AUTHENTICATE: False}
    ):
        response = test_client.get("/api/v1/meta/env")
        payload = response.json
        payload = cast(Dict[str, Any], payload)

        assert payload["env"][SettingsVar.GRAFANA_PANEL_URL.value] == "abc"


def test_versions(test_client: flask.testing.FlaskClient):  # noqa: F811
    response = test_client.get("/api/v1/meta/versions")
    payload = response.json
    payload = cast(Dict[str, Any], payload)

    assert tuple(payload["server"]) == CURRENT_VERSION
    assert tuple(payload["min_client_supported"]) == MIN_CLIENT_SERVER_SUPPORTS
