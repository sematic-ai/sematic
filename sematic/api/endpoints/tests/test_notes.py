# Standard Library
import json

# Third-party
import flask.testing
import pytest
from sqlalchemy.orm.exc import NoResultFound

# Sematic
from sematic.api.tests.fixtures import (  # noqa: F401
    make_auth_test,
    mock_auth,
    test_client,
)
from sematic.db.models.note import Note
from sematic.db.models.run import Run
from sematic.db.models.user import User  # noqa: F401
from sematic.db.queries import get_note, save_note  # noqa: F401
from sematic.db.tests.fixtures import (  # noqa: F401
    persisted_run,
    persisted_user,
    run,
    test_db,
)

test_list_note_auth = make_auth_test("/api/v1/notes")
test_create_note_auth = make_auth_test("/api/v1/notes", method="POST")


def test_list_notes_empty(
    mock_auth, test_client: flask.testing.FlaskClient  # noqa: F811
):
    response = test_client.get("/api/v1/notes")

    assert response.json == dict(content=[], authors=[])


def test_create_note(
    mock_auth, test_client: flask.testing.FlaskClient, persisted_run: Run  # noqa: F811
):
    note_payload = {
        "note": "And now for something completely different",
        "run_id": persisted_run.id,
        "root_id": persisted_run.id,
    }

    response = test_client.post("/api/v1/notes", json=dict(note=note_payload))

    assert response.status_code == 200

    assert response.json is not None
    response_note = response.json["content"]

    for field, value in note_payload.items():
        assert response_note[field] == value

    assert response_note["created_at"] is not None
    assert response_note["updated_at"] is not None


@pytest.fixture
def note(persisted_run: Run, persisted_user: User) -> Note:  # noqa: F811
    return Note(
        user_id=persisted_user.id,
        note="And now for something completely different",
        run_id=persisted_run.id,
        root_id=persisted_run.id,
    )


@pytest.fixture
def persisted_note(note: Note) -> Note:
    save_note(note)
    return note


def test_list_notes(
    mock_auth,  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811
    persisted_note: Note,  # noqa: F811
):
    filters = {"root_id": {"eq": persisted_note.root_id}}
    response = test_client.get("/api/v1/notes?filters=" + json.dumps(filters))

    assert response.json is not None
    assert len(response.json["content"]) == 1
    assert response.json["content"][0]["id"] == persisted_note.id

    assert len(response.json["authors"]) == 1
    assert response.json["authors"][0]["id"] == persisted_note.user_id


def test_delete_note(
    mock_auth,  # noqa: F811
    test_client: flask.testing.FlaskClient,  # noqa: F811
    persisted_note: Note,  # noqa: F811
):

    response = test_client.delete("/api/v1/notes/{}".format(persisted_note.id))

    assert response.status_code == 200

    with pytest.raises(NoResultFound):
        get_note(persisted_note.id)
