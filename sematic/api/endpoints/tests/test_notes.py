# Third-party
import json
import flask.testing
import pytest
from sqlalchemy.orm.exc import NoResultFound

# Sematic
from sematic.api.tests.fixtures import test_client  # noqa: F401
from sematic.db.queries import get_note, save_note  # noqa: F401
from sematic.db.tests.fixtures import test_db, persisted_run, run  # noqa: F401
from sematic.db.models.run import Run
from sematic.db.models.note import Note


def test_list_notes_empty(test_client: flask.testing.FlaskClient):  # noqa: F811
    response = test_client.get("/api/v1/notes")

    assert response.json == dict(
        content=[],
    )


def test_create_note(
    test_client: flask.testing.FlaskClient, persisted_run: Run  # noqa: F811
):
    note_payload = {
        "author_id": "test@test.test",
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
def note(persisted_run: Run) -> Note:  # noqa: F811
    return Note(
        author_id="test@test.test",
        note="And now for something completely different",
        run_id=persisted_run.id,
        root_id=persisted_run.id,
    )


@pytest.fixture
def persisted_note(note: Note) -> Note:
    save_note(note)
    return note


def test_list_notes(
    test_client: flask.testing.FlaskClient, persisted_note: Note  # noqa: F811
):
    filters = {"root_id": {"eq": persisted_note.root_id}}
    response = test_client.get("/api/v1/notes?filters=" + json.dumps(filters))

    assert response.json is not None
    assert len(response.json["content"]) == 1
    assert response.json["content"][0]["id"] == persisted_note.id


def test_delete_note(
    test_client: flask.testing.FlaskClient, persisted_note: Note  # noqa: F811
):

    response = test_client.delete("/api/v1/notes/{}".format(persisted_note.id))

    assert response.status_code == 200

    with pytest.raises(NoResultFound):
        get_note(persisted_note.id)
