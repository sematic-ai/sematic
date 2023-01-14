# Standard Library
import logging
from http import HTTPStatus
from typing import Optional

# Third-party
import flask

# Sematic
from sematic.api.app import sematic_api
from sematic.api.endpoints.auth import authenticate
from sematic.api.endpoints.request_parameters import jsonify_error
from sematic.db.models.external_resource import ExternalResource
from sematic.db.models.user import User
from sematic.db.queries import (
    get_external_resource_record,
    save_external_resource_record,
)
from sematic.plugins.abstract_external_resource import ManagedBy

logger = logging.getLogger(__name__)


@sematic_api.route("/api/v1/external_resources/<resource_id>", methods=["GET"])
@authenticate
def get_resource_endpoint(user: Optional[User], resource_id: str) -> flask.Response:
    refresh_remote = flask.request.args.get("refresh_remote", "false").lower() == "true"

    record = get_external_resource_record(resource_id=resource_id)
    if record is None:
        return jsonify_error(f"No such resource: {resource_id}", HTTPStatus.NOT_FOUND)

    updated_resource = None
    if (
        record.managed_by is ManagedBy.SERVER
        and refresh_remote
        and not record.resource_state.is_terminal()
    ):
        logger.info(
            "Updating resource '%s', currently in state '%s'",
            record.id,
            record.resource_state.value,
        )
        try:
            updated_resource = record.resource.update()
            logger.info(
                "Done updating resource '%s', now in state '%s': %s",
                record.id,
                record.resource_state.value,
                record.status_message,
            )
        except Exception as e:
            logger.exception("Error updating resource '%s': %s", record.id, e)
            return jsonify_error(
                f"Error updating resource: {resource_id}",
                HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    if updated_resource is not None:
        record = ExternalResource.from_resource(updated_resource)
        save_external_resource_record(record)

    payload = dict(external_resource=record.to_json_encodable())

    return flask.jsonify(payload)


@sematic_api.route(
    "/api/v1/external_resources/<resource_id>/activate", methods=["POST"]
)
@authenticate
def activate_resource_endpoint(
    user: Optional[User], resource_id: str
) -> flask.Response:

    record = get_external_resource_record(resource_id=resource_id)
    if record is None:
        return jsonify_error(
            "No such resource: {}".format(resource_id), HTTPStatus.NOT_FOUND
        )
    try:
        activated = record.resource.activate(is_local=False)
    except Exception as e:
        message = "Error activating resource {}: {}".format(resource_id, e)
        logger.exception(message)
        return jsonify_error(
            message,
            HTTPStatus.INTERNAL_SERVER_ERROR,
        )
    record = ExternalResource.from_resource(activated)
    record = save_external_resource_record(record)
    payload = dict(external_resource=record.to_json_encodable())  # type: ignore

    return flask.jsonify(payload)


@sematic_api.route(
    "/api/v1/external_resources/<resource_id>/deactivate", methods=["POST"]
)
@authenticate
def deactivate_resource_endpoint(
    user: Optional[User], resource_id: str
) -> flask.Response:

    record = get_external_resource_record(resource_id=resource_id)
    if record is None:
        return jsonify_error(
            "No such resource: {}".format(resource_id), HTTPStatus.NOT_FOUND
        )

    if record.resource_state.is_terminal():
        payload = dict(external_resource=record.to_json_encodable())  # type: ignore
        return flask.jsonify(payload)

    try:
        deactivated = record.resource.deactivate()
    except Exception as e:
        message = "Error deactivating resource {}: {}".format(resource_id, e)
        logger.exception(message)
        return jsonify_error(
            message,
            HTTPStatus.INTERNAL_SERVER_ERROR,
        )
    record = ExternalResource.from_resource(deactivated)
    record = save_external_resource_record(record)
    payload = dict(external_resource=record.to_json_encodable())  # type: ignore

    return flask.jsonify(payload)


@sematic_api.route("/api/v1/external_resources", methods=["POST"])
@authenticate
def save_resource_endpoint(user: Optional[User]) -> flask.Response:
    if (
        not flask.request
        or not flask.request.json
        or "external_resource" not in flask.request.json
    ):
        return jsonify_error(
            "Request should have 'external_resource' key", HTTPStatus.BAD_REQUEST
        )

    record_json_encodable = flask.request.json["external_resource"]
    record = ExternalResource.from_json_encodable(record_json_encodable)
    record = save_external_resource_record(record)
    payload = dict(external_resource=record.to_json_encodable())

    return flask.jsonify(payload)
