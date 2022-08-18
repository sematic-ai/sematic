# Standard Library
import typing

# Third-party
import flask.testing

# Sematic
from sematic.api.tests.fixtures import (  # noqa: F401
    make_auth_test,
    mock_no_auth,
    mock_requests,
    test_client,
)
from sematic.db.models.resolution import Resolution
from sematic.db.tests.fixtures import (  # noqa: F401
    make_resolution,
    persisted_resolution,
    persisted_run,
    pg_mock,
    resolution,
    run,
    test_db,
)

test_get_resolution_auth = make_auth_test("/api/v1/resolutions/123")
test_put_resolution_auth = make_auth_test("/api/v1/resolutions/123", method="PUT")


@mock_no_auth
def test_get_resolution_endpoint(
    persisted_resolution: Resolution,  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811
):
    response = test_client.get(
        "/api/v1/resolutions/{}".format(persisted_resolution.root_id)
    )

    payload = response.json
    payload = typing.cast(typing.Dict[str, typing.Any], payload)

    assert payload["content"]["root_id"] == persisted_resolution.root_id


@mock_no_auth
def test_get_resolution_404(test_client: flask.testing.FlaskClient):  # noqa: F811
    response = test_client.get("/api/v1/resolutions/unknownid")

    assert response.status_code == 404

    payload = response.json
    payload = typing.cast(typing.Dict[str, typing.Any], payload)

    assert payload == dict(error="No resolutions with id 'unknownid'")
