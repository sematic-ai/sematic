"""
Module keeping all /api/v*/runs/* API endpoints.
"""

# Standard Library
from http import HTTPStatus
from typing import Optional

# Third-party
import flask
import flask_socketio  # type: ignore
import sqlalchemy
from sqlalchemy.orm.exc import NoResultFound

# Sematic
from sematic.abstract_future import FutureState
from sematic.api.app import sematic_api
from sematic.api.endpoints.auth import authenticate
from sematic.api.endpoints.request_parameters import jsonify_error
from sematic.db.models.resolution import InvalidResolution, Resolution, ResolutionStatus
from sematic.db.models.run import Run
from sematic.db.models.user import User
from sematic.db.queries import (
    get_graph,
    get_resolution,
    get_run,
    save_graph,
    save_resolution,
)
from sematic.scheduling.job_scheduler import schedule_resolution
from sematic.scheduling.kubernetes import cancel_job


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
        return jsonify_error(
            "Please provide a resolution payload in JSON format.",
            HTTPStatus.BAD_REQUEST,
        )

    resolution_json_encodable = flask.request.json["resolution"]
    resolution = Resolution.from_json_encodable(resolution_json_encodable)

    if not resolution.root_id == resolution_id:
        return jsonify_error(
            f"Id of resolution in the payload ({resolution.root_id}) does not match "
            f"the one from the endpoint called ({resolution_id})",
            HTTPStatus.BAD_REQUEST,
        )

    try:
        root_run = get_run(resolution_id)
        if root_run.parent_id is not None:
            return jsonify_error(
                f"Resolutions can only be created for root runs, but the run "
                f"{root_run.id} has parent {root_run.parent_id}",
                HTTPStatus.BAD_REQUEST,
            )
    except NoResultFound:
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
        return jsonify_error(str(e), HTTPStatus.BAD_REQUEST)

    save_resolution(resolution)

    return flask.jsonify({})


@sematic_api.route("/api/v1/resolutions/<resolution_id>/schedule", methods=["POST"])
@authenticate
def schedule_resolution_endpoint(
    user: Optional[User], resolution_id: str
) -> flask.Response:
    resolution = get_resolution(resolution_id)

    resolution = schedule_resolution(resolution)

    save_resolution(resolution)

    payload = dict(
        content=resolution.to_json_encodable(),
    )

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

    if not ResolutionStatus.is_allowed_transition(
        from_status=resolution.status, to_status=ResolutionStatus.CANCELED
    ):
        return jsonify_error(
            f"Resolution cannot be canceled. Current state: {resolution.status}",
            HTTPStatus.BAD_REQUEST,
        )

    root_run = get_run(resolution.root_id)

    terminal_states = (
        future_state.value for future_state in FutureState if future_state.is_terminal()
    )

    unfinished_runs, _, __ = get_graph(
        sqlalchemy.and_(
            Run.root_id == resolution.root_id,
            sqlalchemy.not_(Run.future_state.in_(terminal_states)),  # type: ignore
        ),
        include_edges=False,
        include_artifacts=False,
    )

    for external_job in resolution.external_jobs:
        cancel_job(external_job)

    resolution.status = ResolutionStatus.CANCELED
    save_resolution(resolution)

    for run in unfinished_runs:
        for external_job in run.external_jobs:
            cancel_job(external_job)

        run.future_state = FutureState.CANCELED

    save_graph(unfinished_runs, [], [])

    flask_socketio.emit(
        "update",
        dict(run_id=resolution.root_id),
        namespace="/graph",
        broadcast=True,
    )

    flask_socketio.emit(
        "cancel",
        dict(
            resolution_id=resolution.root_id, calculator_path=root_run.calculator_path
        ),
        namespace="/pipeline",
        broadcast=True,
    )

    return flask.jsonify(dict(content=resolution.to_json_encodable()))
