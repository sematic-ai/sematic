# Standard Library
import logging
import time
from enum import Enum, unique
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
    get_orphaned_resource_records,
    save_external_resource_record,
)
from sematic.plugins.abstract_external_resource import (
    AbstractExternalResource,
    ManagedBy,
    ResourceState,
)

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
        logger.info(
            "After calling 'activate' resource %s is in state: %s",
            activated.id,
            activated.status.state,
        )
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


@sematic_api.route("/api/v1/external_resources/orphaned", methods=["GET"])
@authenticate
def get_orphaned_resources_endpoint(user: Optional[User]) -> flask.Response:
    resources = get_orphaned_resource_records()
    return flask.jsonify({"content": [resource.id for resource in resources]})


@sematic_api.route("/api/v1/external_resources/<resource_id>/clean", methods=["POST"])
@authenticate
def clean_resource_endpoint(user: Optional[User], resource_id: str) -> flask.Response:
    resource = get_external_resource_record(resource_id)
    if resource is None:
        return jsonify_error(f"No such resource: {resource_id}", HTTPStatus.NOT_FOUND)
    force = flask.request.args.get("force", "false").lower() == "true"

    try:
        clean_result = deactivate_resource(resource, force)
    except Exception:
        logger.exception("Error cleaning resource %s", resource_id)
        clean_result = CleanResult.UPDATE_ERROR
        if force:
            clean_result = CleanResult.FORCED_TERMINAL
            resource.force_to_terminal_state("Cleaning resource.")
            save_external_resource_record(resource)
    return flask.jsonify({"content": clean_result.value})


@unique
class CleanResult(Enum):
    DEACTIVATED = "DEACTIVATED"
    UNMODIFIED = "UNMODIFIED"
    UPDATE_ERROR = "UPDATE_ERROR"
    FORCED_TERMINAL = "FORCED_TERMINAL"


def deactivate_resource(resource: ExternalResource, force: bool) -> CleanResult:
    """Deactivate the resource if possible.

    Parameters
    ----------
    resource:
        The resource to deactivate.
    force:
        If true, will force the resource's metadata to a terminal state
        regardless of whether the deactivation could be verified.

    Returns
    -------
    CleanResult indicating the result of the attempt to clean the resource.
    """
    if (
        resource.resource_state != ResourceState.CREATED
        and resource.managed_by != ManagedBy.SERVER
    ):
        logger.info("Skipping clean of %s, not managed by server", resource.id)
        return CleanResult.UNMODIFIED

    abstract_resource: AbstractExternalResource = resource.resource
    if abstract_resource.status.state.is_terminal():
        logger.info(
            "Skipping clean of %s, in terminal state %s",
            resource.id,
            abstract_resource.status.state,
        )
        return CleanResult.UNMODIFIED
    if abstract_resource.status.state != ResourceState.DEACTIVATING:
        abstract_resource = abstract_resource.deactivate()
        resource.resource = abstract_resource
        save_external_resource_record(resource)

    abstract_resource = wait_for_deactivation(
        abstract_resource, abstract_resource.get_deactivation_timeout_seconds()
    )
    resource.resource = abstract_resource
    save_external_resource_record(resource)
    if abstract_resource.status.state.is_terminal():
        return CleanResult.DEACTIVATED
    else:
        return CleanResult.UPDATE_ERROR


def wait_for_deactivation(
    resource: AbstractExternalResource, timeout_seconds: float
) -> AbstractExternalResource:
    start = time.time()
    while time.time() - start < timeout_seconds:
        resource = resource.update()
        if resource.status.state.is_terminal():
            break
    return resource
