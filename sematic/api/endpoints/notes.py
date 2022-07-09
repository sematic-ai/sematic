# Standard library
import json
from typing import List
from http import HTTPStatus

# Third-party
import flask
import sqlalchemy
from sqlalchemy.orm.exc import NoResultFound

# Sematic
from sematic.api.app import sematic_api
from sematic.api.endpoints.request_parameters import (
    get_request_parameters,
    jsonify_error,
)
from sematic.db.models.note import Note
from sematic.db.models.run import Run
from sematic.db.db import db
from sematic.db.queries import delete_note, get_note, save_note


@sematic_api.route("/api/v1/notes", methods=["GET"])
def list_notes_endpoint() -> flask.Response:
    limit, _, _, sql_predicates = get_request_parameters(
        flask.request.args,
        Note,
    )
    with db().get_session() as session:
        query = session.query(Note)

        if sql_predicates is not None:
            query = query.filter(sql_predicates)

        if "calculator_path" in flask.request.args:
            query = query.join(Run, Run.id == Note.root_id).filter(
                Run.calculator_path == flask.request.args["calculator_path"]
            )

        query = query.order_by(sqlalchemy.asc(Note.created_at))

        # query = query.limit(limit)

        notes: List[Note] = query.all()

    payload = dict(content=[note.to_json_encodable() for note in notes])

    return flask.jsonify(payload)


@sematic_api.route("/api/v1/notes", methods=["POST"])
def create_note_endpoint() -> flask.Response:
    if not flask.request or not flask.request.json or "note" not in flask.request.json:
        return flask.Response(
            json.dumps(dict(error="Malformed payload")),
            status=HTTPStatus.BAD_REQUEST.value,
            mimetype="application/json",
        )

    note_json = flask.request.json["note"]

    try:
        note = Note.from_json_encodable(note_json)
    except Exception as exc:
        return flask.Response(
            json.dumps(dict(error=f"Note failed to create: {exc}.")),
            status=HTTPStatus.BAD_REQUEST.value,
            mimetype="application/json",
        )

    save_note(note)

    return flask.jsonify(dict(content=note.to_json_encodable()))


@sematic_api.route("/api/v1/notes/<note_id>", methods=["DELETE"])
def delete_note_endpoint(note_id: str) -> flask.Response:
    try:
        note = get_note(note_id)
    except NoResultFound:
        return jsonify_error("No such note: {}".format(note_id), HTTPStatus.NOT_FOUND)

    delete_note(note)

    return flask.jsonify({})
