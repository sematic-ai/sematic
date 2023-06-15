# Standard Library
from typing import List

# Third-party
import flask.testing
import pytest

# Sematic
from sematic.api.tests.fixtures import test_client  # noqa: F401
from sematic.db.db import DB
from sematic.db.models.organization import Organization
from sematic.db.tests.fixtures import test_db  # noqa: F401


@pytest.fixture
def org_fixtures(test_db: DB):  # noqa: F811
    orgs = [
        Organization(id="0", name="DS", kubernetes_namespace="ds"),
        Organization(id="1", name="Eng", kubernetes_namespace="eng"),
        Organization(id="2", name="HR", kubernetes_namespace=None),
    ]

    with test_db.get_session() as session:
        session.add_all(orgs)
        session.commit()

        for org in orgs:
            session.refresh(org)

    return orgs


def test_list_organizations(
    org_fixtures: List[Organization],
    test_client: flask.testing.FlaskClient,  # noqa: F811
):
    response = test_client.get("/api/v1/organizations")

    orgs = response.json["content"]  # type: ignore

    assert orgs[0]["id"] == "0"
    assert orgs[0]["name"] == "DS"
    assert orgs[0]["kubernetes_namespace"] == "ds"

    assert orgs[1]["id"] == "1"
    assert orgs[1]["name"] == "Eng"
    assert orgs[1]["kubernetes_namespace"] == "eng"

    assert orgs[2]["id"] == "2"
    assert orgs[2]["name"] == "HR"
    assert orgs[2]["kubernetes_namespace"] is None
