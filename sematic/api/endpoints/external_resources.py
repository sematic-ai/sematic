# Standard Library
import logging
import time
from dataclasses import asdict, dataclass
from http import HTTPStatus
from typing import List, Optional

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


@sematic_api.route("/api/v1/external_resources/all/clean_orphaned", methods=["POST"])
@authenticate
def clean_orphaned_resources_endpoint(user: Optional[User]) -> flask.Response:
    resources = get_orphaned_resource_records()
    force = flask.request.args.get("force", "false").lower() == "true"
    state_changes = deactivate_resources(resources, force)
    return flask.jsonify({"state_changes": asdict(state_changes)})


@dataclass
class StateChanges:
    deactivated: List[str]
    unmodified: List[str]
    update_error: List[str]
    forced_terminal: List[str]


def deactivate_resources(
    resources: List[ExternalResource], force: bool
) -> StateChanges:
    state_changes = StateChanges(
        deactivated=[],
        unmodified=[],
        update_error=[],
        forced_terminal=[],
    )
    for resource in resources:
        ended_terminal = False
        try:
            ended_terminal = deactivate_resource(resource, state_changes)
        except Exception:
            logger.exception("Error evolving deactivation for '%s'", resource.id)
            state_changes.update_error.append(resource.id)
        if force and not ended_terminal:
            logger.warning("Forcing resource %s into terminal state.", resource.id)
            try:
                resource.force_to_terminal_state("Resources were being cleaned.")
                save_external_resource_record(resource)
                state_changes.forced_terminal.append(resource.id)
            except Exception:
                logger.exception(
                    "Error forcing resource %s into terminal state.", resource.id
                )
    logger.info("Done cleaning resources: %s", state_changes)
    return state_changes


def deactivate_resource(
    resource: ExternalResource, state_changes: StateChanges
) -> bool:
    """Deactivate the resource if possible, and update state_changes.

    Parameters
    ----------
    resource:
        The resource to deactivate.
    state_changes:
        A dict of state changes to update depending on how the resource's state is
        evolved.

    Returns
    -------
    True if the resource ended in a terminal state, False otherwise.
    """
    if resource.managed_by != ManagedBy.SERVER:
        state_changes.unmodified.append(resource.id)
        logger.info("Skipping clean of %s, not managed by server", resource.id)
        return resource.resource_state.is_terminal()

    abstract_resource: AbstractExternalResource = resource.resource
    if abstract_resource.status.state.is_terminal():
        logger.info(
            "Skipping clean of %s, in terminal state %s",
            resource.id,
            abstract_resource.status.state,
        )
        state_changes.unmodified.append(resource.id)
        return resource.resource_state.is_terminal()
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
        state_changes.deactivated.append(abstract_resource.id)
    else:
        state_changes.update_error.append(abstract_resource.id)
    return abstract_resource.status.state.is_terminal()


def wait_for_deactivation(
    resource: AbstractExternalResource, timeout_seconds: float
) -> AbstractExternalResource:
    start = time.time()
    while time.time() - start < timeout_seconds:
        resource = resource.update()
        if resource.status.state.is_terminal():
            break
    return resource
