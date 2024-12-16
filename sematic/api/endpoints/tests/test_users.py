# Standard Library
from typing import List

# Third-party
import flask.testing
import pytest

# Sematic
from sematic.api.tests.fixtures import test_client  # noqa: F401
from sematic.db.db import DB
from sematic.db.models.user import User
from sematic.db.tests.fixtures import test_db  # noqa: F401


@pytest.fixture
def the_beatles(test_db: DB):  # noqa: F811
    users = [
        User(
            id="0",
            email="paul@thebeatles.co.uk",
            first_name="Paul",
            last_name="McCartney",
            api_key="0",
        ),
        User(
            id="1",
            email="george@thebeatles.co.uk",
            first_name="George",
            last_name="Harrison",
            api_key="1",
        ),
        User(
            id="2",
            email="john@thebeatles.co.uk",
            first_name="John",
            last_name="Lennon",
            api_key="2",
        ),
        User(
            id="3",
            email="ringo@thebeatles.co.uk",
            first_name="Ringo",
            last_name="Starr",
            api_key="3",
        ),
    ]

    with test_db.get_session() as session:
        session.add_all(users)
        session.commit()

        for user in users:
            session.refresh(user)

    return users


def test_list_users(
    the_beatles: List[User],
    test_client: flask.testing.FlaskClient,  # noqa: F811
):
    response = test_client.get("/api/v1/users")

    users = response.json["content"]  # type: ignore

    assert [user["first_name"] for user in users] == ["George", "John", "Paul", "Ringo"]

    for user in users:
        assert "api_key" not in user
        assert "email" not in user
