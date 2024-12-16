# Standard Library
from typing import Any, Dict, cast

# Third-party
import flask.testing
import sqlalchemy

# Sematic
import sematic.api.endpoints.meta  # noqa: F401
from sematic.api.app import sematic_api  # noqa: F401
from sematic.api.tests.fixtures import (
    mock_requests,  # noqa: F401
    mock_server_settings,  # noqa: F401
    test_client,  # noqa: F401
)
from sematic.config.server_settings import ServerSettingsVar
from sematic.db.db import DB
from sematic.db.tests.fixtures import persisted_user, test_db  # noqa: F401
from sematic.versions import CURRENT_VERSION, MIN_CLIENT_SERVER_SUPPORTS


def test_env(test_client: flask.testing.FlaskClient):  # noqa: F811
    with mock_server_settings(
        {
            ServerSettingsVar.GRAFANA_PANEL_URL: "abc",
            ServerSettingsVar.SEMATIC_AUTHENTICATE: "false",
        }
    ):
        response = test_client.get("/api/v1/meta/env")
        payload = response.json
        payload = cast(Dict[str, Any], payload)

        assert payload["env"][ServerSettingsVar.GRAFANA_PANEL_URL.value] == "abc"


def test_versions(test_client: flask.testing.FlaskClient):  # noqa: F811
    response = test_client.get("/api/v1/meta/versions")
    payload = response.json
    payload = cast(Dict[str, Any], payload)

    assert tuple(payload["server"]) == CURRENT_VERSION
    assert tuple(payload["min_client_supported"]) == MIN_CLIENT_SERVER_SUPPORTS


def test_health(
    test_client: flask.testing.FlaskClient,  # noqa: F811
    test_db: DB,  # noqa: F811
):
    response = test_client.get("/api/v1/meta/health")
    payload = response.json
    assert response.status_code == 200
    payload = cast(Dict[str, Any], payload)
    assert payload == {
        "api": {"healthy": True, "message": "API is healthy"},
        "db": {"healthy": True, "message": "Basic database access verified"},
    }

    with test_db.get_session() as session:
        statement = sqlalchemy.text("DROP TABLE runs;")
        session.execute(statement)

    response = test_client.get("/api/v1/meta/health")
    payload = response.json
    assert response.status_code == 200
    payload = cast(Dict[str, Any], payload)
    assert payload["api"] == {"healthy": True, "message": "API is healthy"}
    assert not payload["db"]["healthy"]
    assert "no such table" in payload["db"]["message"]
