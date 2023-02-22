"""
Module keeping all /api/v*/runs/* API endpoints.
"""

# Standard Library
import logging
from http import HTTPStatus
from typing import Optional

# Third-party
import flask
import sqlalchemy
from sqlalchemy.orm.exc import NoResultFound

# Sematic
from sematic.abstract_future import FutureState
from sematic.api.app import sematic_api
from sematic.api.endpoints.auth import authenticate
from sematic.api.endpoints.events import (
    broadcast_graph_update,
    broadcast_pipeline_update,
    broadcast_resolution_cancel,
)
from sematic.api.endpoints.request_parameters import jsonify_error
from sematic.db.models.factories import clone_resolution, clone_root_run
from sematic.db.models.resolution import InvalidResolution, Resolution, ResolutionStatus
from sematic.db.models.run import Run
from sematic.db.models.user import User
from sematic.db.queries import (
    get_graph,
    get_resolution,
    get_resources_by_root_id,
    get_run,
    get_run_graph,
    save_graph,
    save_resolution,
)
from sematic.plugins.abstract_publisher import get_publishing_plugins
from sematic.scheduling.job_scheduler import schedule_resolution
from sematic.scheduling.kubernetes import cancel_job

logger = logging.getLogger(__name__)


@sematic_api.route("/api/v1/resolutions/<resolution_id>", methods=["GET"])
@authenticate
def get_resolution_endpoint(user: Optional[User], resolution_id: str) -> flask.Response:
    try:
        resolution = get_resolution(resolution_id)
    except NoResultFound:
        return jsonify_error(
            "No resolutions with id {}".format(repr(resolution_id)),
            HTTPStatus.NOT_FOUND,
        )

    resolution_json = resolution.to_json_encodable()

    # Scrub the environment variables before returning from the
    # API. They can contain sensitive info like API keys. On write,
    # we consider this field to be immutable, so we will just re-use
    # whatever was already in the DB for it
    resolution_json[Resolution.settings_env_vars.key] = {}

    payload = dict(
        content=resolution_json,
    )

    return flask.jsonify(payload)


@sematic_api.route("/api/v1/resolutions/<resolution_id>", methods=["PUT"])
@authenticate
def put_resolution_endpoint(user: Optional[User], resolution_id: str) -> flask.Response:
    if (
        not flask.request
        or not flask.request.json
        or "resolution" not in flask.request.json
    ):
        logger.warning("No json resolution payload")
        return jsonify_error(
            "Please provide a resolution payload in JSON format.",
            HTTPStatus.BAD_REQUEST,
        )

    resolution_json_encodable = flask.request.json["resolution"]
    resolution = Resolution.from_json_encodable(resolution_json_encodable)

    if user is not None:
        resolution.user_id = user.id

    if not resolution.root_id == resolution_id:
        message = (
            f"Id of resolution in the payload ({resolution.root_id}) does not match "
            f"the one from the endpoint called ({resolution_id})"
        )
        logger.warning(message)
        return jsonify_error(
            message,
            HTTPStatus.BAD_REQUEST,
        )

    try:
        root_run = get_run(resolution_id)
        if root_run.parent_id is not None:
            logger.warning("Non-root run resolution reference")
            return jsonify_error(
                f"Resolutions can only be created for root runs, but the run "
                f"{root_run.id} has parent {root_run.parent_id}",
                HTTPStatus.BAD_REQUEST,
            )
    except NoResultFound:
        logger.warning("No resolution with given id: %s", resolution_id)
        return jsonify_error(
            f"Resolutions can only be created when there is an existing run they "
            f"are resolving, but there is no run with id {resolution_id}",
            HTTPStatus.BAD_REQUEST,
        )

    try:
        existing_resolution = get_resolution(resolution_id)
    except NoResultFound:
        existing_resolution = None

    try:
        if existing_resolution is not None:
            # This field is scrubbed on read, but should be immutable.
            # ignore whatever the caller sent back this time.
            resolution.settings_env_vars = existing_resolution.settings_env_vars
            existing_resolution.update_with(resolution)
            resolution = existing_resolution
        else:
            resolution.validate_new()
    except InvalidResolution as e:
        logger.warning("Could not update resolution: %s", e)
        return jsonify_error(str(e), HTTPStatus.BAD_REQUEST)

    if ResolutionStatus[resolution.status].is_terminal():
        try:
            _cancel_non_terminal_runs(resolution.root_id)
        except Exception as e:
            logger.exception("Error when trying to cancel runs in resolution: %s", e)

    save_resolution(resolution)
    _publish_resolution_event(resolution)

    return flask.jsonify({})


@sematic_api.route("/api/v1/resolutions/<resolution_id>/schedule", methods=["POST"])
@authenticate
def schedule_resolution_endpoint(
    user: Optional[User], resolution_id: str
) -> flask.Response:
    resolution = get_resolution(resolution_id)

    max_parallelism, rerun_from = None, None

    if flask.request.json:
        if "max_parallelism" in flask.request.json:
            max_parallelism = flask.request.json["max_parallelism"]

        if "rerun_from" in flask.request.json:
            rerun_from = flask.request.json["rerun_from"]

    resolution = schedule_resolution(
        resolution=resolution, max_parallelism=max_parallelism, rerun_from=rerun_from
    )

    save_resolution(resolution)

    payload = dict(
        content=resolution.to_json_encodable(),
    )

    return flask.jsonify(payload)


@sematic_api.route("/api/v1/resolutions/<resolution_id>/rerun", methods=["POST"])
@authenticate
def rerun_resolution_endpoint(
    user: Optional[User], resolution_id: str
) -> flask.Response:
    original_resolution = get_resolution(resolution_id)

    if original_resolution.container_image_uri is None:
        return jsonify_error(
            (
                f"Resolution {original_resolution.root_id} cannot be re-run: "
                "it was initially resolved locally, and therefore "
                "no container image was built"
            ),
            HTTPStatus.BAD_REQUEST,
        )

    rerun_from = None
    if flask.request.json and "rerun_from" in flask.request.json:
        rerun_from = flask.request.json["rerun_from"]

    original_runs, _, original_edges = get_run_graph(original_resolution.root_id)
    original_root_run = original_runs[0]

    root_run, edges = clone_root_run(original_root_run, original_edges)

    if user is not None:
        root_run.user_id = user.id

    save_graph(runs=[root_run], edges=edges, artifacts=[])

    resolution = clone_resolution(original_resolution, root_id=root_run.id)

    if user is not None:
        resolution.user_id = user.id

    resolution = schedule_resolution(resolution, rerun_from=rerun_from)

    save_resolution(resolution)

    payload = dict(
        content=resolution.to_json_encodable(),
    )

    broadcast_pipeline_update(calculator_path=root_run.calculator_path, user=user)

    return flask.jsonify(payload)


@sematic_api.route("/api/v1/resolutions/<resolution_id>/cancel", methods=["PUT"])
@authenticate
def cancel_resolution_endpoint(
    user: Optional[User], resolution_id: str
) -> flask.Response:
    try:
        resolution = get_resolution(resolution_id)
    except NoResultFound:
        return jsonify_error(
            "No resolutions with id {}".format(repr(resolution_id)),
            HTTPStatus.NOT_FOUND,
        )

    if resolution.status == ResolutionStatus.CANCELED.value:
        logger.info("Resolution is already canceled")
        return flask.jsonify(dict(content=resolution.to_json_encodable()))

    if not ResolutionStatus.is_allowed_transition(
        from_status=resolution.status, to_status=ResolutionStatus.CANCELED
    ):
        message = f"Resolution cannot be canceled. Current state: {resolution.status}"
        logger.warning(message)
        return jsonify_error(message, HTTPStatus.BAD_REQUEST)

    root_run = get_run(resolution.root_id)

    jobs = []
    for external_job in resolution.external_jobs:
        jobs.append(cancel_job(external_job))
    resolution.external_jobs = jobs  # type: ignore

    resolution.status = ResolutionStatus.CANCELED
    save_resolution(resolution)

    _cancel_non_terminal_runs(resolution.root_id)

    broadcast_graph_update(root_id=resolution.root_id, user=user)
    broadcast_resolution_cancel(
        root_id=resolution.root_id, calculator_path=root_run.calculator_path, user=user
    )

    return flask.jsonify(dict(content=resolution.to_json_encodable()))


@sematic_api.route(
    "/api/v1/resolutions/<resolution_id>/external_resources", methods=["GET"]
)
@authenticate
def get_resources_endpoint(user: Optional[User], resolution_id: str) -> flask.Response:
    resources = get_resources_by_root_id(resolution_id)
    payload = dict(
        external_resources=[resource.to_json_encodable() for resource in resources]
    )
    return flask.jsonify(payload)


def _publish_resolution_event(resolution: Resolution) -> None:
    """
    Publishes information about the Resolution state change event to all configured
    external publishers, if any.
    """
    publisher_classes = get_publishing_plugins(default=[])
    if len(publisher_classes) == 0:
        logger.debug("No external Resolution event publishers configured")

    for publisher_class in publisher_classes:
        # TODO: components such as these should be instantiated once at startup and made
        #  available as a server-internal first-class citizen component API
        publisher_class().publish(resolution)


def _cancel_non_terminal_runs(root_id):
    terminal_states = FutureState.terminal_state_strings()

    unfinished_runs, _, __ = get_graph(
        sqlalchemy.and_(
            Run.root_id == root_id,
            sqlalchemy.not_(Run.future_state.in_(terminal_states)),  # type: ignore
        ),
        include_edges=False,
        include_artifacts=False,
    )

    for run in unfinished_runs:
        jobs = []
        for external_job in run.external_jobs:
            jobs.append(cancel_job(external_job))
        run.external_jobs = jobs

        run.future_state = FutureState.CANCELED

    save_graph(unfinished_runs, [], [])
