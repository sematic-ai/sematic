# Standard Library
import json
from dataclasses import dataclass
from typing import Any, Dict, Optional
from unittest import mock

# Third-party
import pytest

# Sematic
from sematic.api_client import (
    IncompatibleClientError,
    ServerError,
    _validate_server_compatibility,
    get_artifact_value_by_id,
)
from sematic.config import get_config
from sematic.db.models.factories import make_artifact
from sematic.tests.fixtures import MockStorage, valid_client_version  # noqa: F401
from sematic.versions import CURRENT_VERSION, MIN_CLIENT_SERVER_SUPPORTS


@dataclass
class MockRequest:
    method: str = "GET"


@dataclass
class MockResponse:
    status_code: int
    json_contents: Dict[str, Any]
    text_contents: Optional[str] = None
    url: str = "http://example.com"
    method: str = "GET"

    def json(self) -> Dict[str, Any]:
        return self.json_contents

    @property
    def text(self) -> str:
        if self.text_contents is None:
            return json.dumps(self.json_contents)
        return self.text_contents

    @property
    def request(self) -> MockRequest:
        return MockRequest(method=self.method)


class ConnectionError(RuntimeError):
    pass


@mock.patch("sematic.api_client.requests")
def test_validate_server_compatibility(mock_requests):
    mock_requests.get.return_value = MockResponse(
        status_code=200,
        json_contents=dict(
            server=CURRENT_VERSION,
            min_client_supported=MIN_CLIENT_SERVER_SUPPORTS,
        ),
    )
    _validate_server_compatibility(seconds_between_tries=0, use_cached=False)
    mock_requests.get.assert_called_with(
        f"{get_config().api_url}/meta/versions",
        headers={"Content-Type": "application/json"},
    )


@mock.patch("sematic.api_client.requests")
def test_validate_server_compatibility_retry(mock_requests):
    mock_requests.get.return_value = MockResponse(status_code=500, json_contents={})
    with pytest.raises(ServerError):
        _validate_server_compatibility(
            tries=5, seconds_between_tries=0, use_cached=False
        )
    assert len(mock_requests.get.call_args_list) == 5


@mock.patch("sematic.api_client.requests")
def test_validate_server_compatibility_bad_json(mock_requests):
    mock_requests.get.return_value = MockResponse(status_code=200, json_contents={})

    def bad_json(*_):
        raise json.JSONDecodeError("", "", 1)

    mock_requests.get.return_value.json = bad_json
    with pytest.raises(IncompatibleClientError):
        _validate_server_compatibility(
            tries=5, seconds_between_tries=0, use_cached=False
        )


@mock.patch("sematic.api_client.requests")
def test_validate_server_compatibility_old_server(mock_requests):
    mock_requests.get.return_value = MockResponse(
        status_code=200,
        json_contents=dict(
            server=(0, 1, 0),
            min_client_supported=(0, 1, 0),
        ),
    )
    with pytest.raises(IncompatibleClientError):
        _validate_server_compatibility(
            tries=5, seconds_between_tries=0, use_cached=False
        )


@mock.patch("sematic.api_client.requests")
def test_validate_server_compatibility_old_client(mock_requests):
    mock_requests.get.return_value = MockResponse(
        status_code=200,
        json_contents=dict(
            server=(2**32, 0, 0),
            # let's HOPE it's safe to assume we will never have billions
            # of major versions...
            min_client_supported=(2**32, 0, 0),
        ),
    )
    with pytest.raises(IncompatibleClientError):
        _validate_server_compatibility(
            tries=5, seconds_between_tries=0, use_cached=False
        )


@mock.patch("sematic.api_client.requests")
def test_validate_server_compatibility_new_server_still_supports(mock_requests):
    mock_requests.get.return_value = MockResponse(
        status_code=200,
        json_contents=dict(
            server=(2**32, 0, 0),
            min_client_supported=MIN_CLIENT_SERVER_SUPPORTS,
        ),
    )
    _validate_server_compatibility(tries=5, seconds_between_tries=0, use_cached=False)


@mock.patch("sematic.api_client.requests")
def test_get_artifact_value_by_id(mock_requests, valid_client_version):  # noqa: F811
    mock_storage = MockStorage()
    artifact = make_artifact(42, int, mock_storage)
    mock_requests.get.return_value = MockResponse(
        status_code=200,
        json_contents=dict(content=artifact.to_json_encodable()),
    )

    value = get_artifact_value_by_id(artifact.id, mock_storage)

    assert isinstance(value, int)
    assert value == 42
