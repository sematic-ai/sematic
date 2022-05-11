# Third-party
import pytest

# Glow
from glow.db.tests.fixtures import test_db  # noqa: F401

# Importing from server instead of app to make sure
# all endpoints are loaded
from glow.api.server import glow_api


@pytest.fixture
def test_client(test_db):  # noqa: F811
    glow_api.config["DATABASE"] = test_db
    glow_api.config["TESTING"] = True

    with glow_api.test_client() as client:
        yield client
