# Standard library
import typing

# Third-party
import flask.testing

# Glow
from glow.api.tests.fixtures import test_client  # noqa: F401
from glow.db.tests.fixtures import test_db, make_run  # noqa: F401
from glow.db.queries import create_run


def test_list_runs_empty(test_client: flask.testing.FlaskClient):  # noqa: F811
    results = test_client.get("/api/v1/runs?limit=3")

    assert results.json == dict(
        current_page_url="http://localhost/api/v1/runs?limit=3",
        next_page_url=None,
        limit=3,
        next_cursor=None,
        after_cursor_count=0,
        content=[],
    )


def test_list_runs(test_client: flask.testing.FlaskClient):  # noqa: F811
    created_runs = [create_run(make_run()) for _ in range(5)]

    # Sort by latest
    created_runs = sorted(created_runs, key=lambda run: run.created_at, reverse=True)

    results = test_client.get("/api/v1/runs?limit=3")

    assert len(results.json["next_page_url"]) > 0
    assert len(results.json["next_cursor"]) > 0
    assert results.json["after_cursor_count"] == len(created_runs)
    assert results.json["content"] == [
        run.to_json_encodable() for run in created_runs[:3]
    ]

    next_page_url = results.json["next_page_url"]
    next_page_url = next_page_url.split("localhost")[1]

    results = test_client.get(next_page_url)
    assert results.json["next_page_url"] is None
    assert results.json["next_cursor"] is None
    assert results.json["after_cursor_count"] == 2
    assert results.json["content"] == [
        run.to_json_encodable() for run in created_runs[3:]
    ]
