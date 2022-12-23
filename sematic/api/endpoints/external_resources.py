# Standard Library
from http import HTTPStatus
from typing import Optional

# Third-party
import flask

# Sematic
from sematic.api.app import sematic_api
from sematic.api.endpoints.auth import authenticate
from sematic.api.endpoints.request_parameters import jsonify_error
from sematic.db.models.external_resource import (
    ExternalResource as ExternalResourceRecord,
)
from sematic.db.models.user import User
from sematic.db.queries import (
    get_external_resource_record,
    get_resource_ids_by_root_id,
    save_external_resource_record,
    save_run_external_resource_link,
)

ROOT_ID_KEY = "root_id"


# Allow getting a list of external resource ids.
# Q: Why not just return the actual resources?
# A: Because we should have the endpoint for getting an external resource
#    hooked up such that it actually interacts with the external compute
#    to get the most up-to-date status of the records. It would be too much work
#    for one service call to have to do that for a *list* of resources.
# Q: Ok, then why not just return the resources without updating them for this?
# A: Because it would be weird to have the server return stale states when queried
#    in a list but up-to-date ones when queried one-by-one.
@sematic_api.route("/api/v1/external_resources/ids", methods=["GET"])
@authenticate
def get_resources_endpoint(user: Optional[User]) -> flask.Response:
    if set(flask.request.args.keys()) != {ROOT_ID_KEY}:
        return jsonify_error(
            f"Can only get external resources using the query key {ROOT_ID_KEY} ",
            HTTPStatus.BAD_REQUEST,
        )

    resource_ids = get_resource_ids_by_root_id(flask.request.args[ROOT_ID_KEY])
    payload = dict(resource_ids=resource_ids)
    return flask.jsonify(payload)


@sematic_api.route("/api/v1/external_resources/<resource_id>", methods=["GET"])
@authenticate
def get_resource_endpoint(user: Optional[User], resource_id: str) -> flask.Response:
    record = get_external_resource_record(resource_id=resource_id)
    if record is None:
        return jsonify_error(
            "No such resource: {}".format(resource_id), HTTPStatus.NOT_FOUND
        )

    payload = dict(record=record.to_json_encodable())

    return flask.jsonify(payload)


@sematic_api.route("/api/v1/external_resources/<resource_id>", methods=["POST"])
@authenticate
def save_resource_endpoint(user: Optional[User], resource_id: str) -> flask.Response:
    if (
        not flask.request
        or not flask.request.json
        or "record" not in flask.request.json
    ):
        return jsonify_error("Request should have 'record' key", HTTPStatus.BAD_REQUEST)

    record_json_encodable = flask.request.json["record"]
    record = ExternalResourceRecord.from_json_encodable(record_json_encodable)

    if record.id != resource_id:
        return jsonify_error(
            "Resource id should match serialized resource record",
            HTTPStatus.BAD_REQUEST,
        )
    record = save_external_resource_record(record)
    payload = dict(record=record.to_json_encodable())

    return flask.jsonify(payload)


@sematic_api.route(
    "/api/v1/external_resources/<resource_id>/linked_run/<run_id>", methods=["POST"]
)
@authenticate
def save_resource_run_link_endpoint(
    user: Optional[User], resource_id: str, run_id: str
) -> flask.Response:
    save_run_external_resource_link(resource_id, run_id)
    return flask.jsonify({"run_id": run_id, "resource_id": resource_id})
