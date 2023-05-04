"""
Module keeping all /api/v*/runs/* API endpoints.
"""

# Standard Library
import logging
from datetime import datetime
from http import HTTPStatus
from typing import Optional, Tuple, Union
from urllib.parse import urlencode

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
from sematic.api.endpoints.payloads import get_resolution_payload
from sematic.api.endpoints.request_parameters import (
    get_gc_filters,
    jsonify_error,
    list_garbage_ids,
)
from sematic.config.settings import MissingSettingsError
from sematic.config.user_settings import UserSettingsVar
from sematic.db.models.factories import clone_resolution, clone_root_run
from sematic.db.models.resolution import InvalidResolution, Resolution, ResolutionStatus
from sematic.db.models.run import Run
from sematic.db.models.user import User
from sematic.db.queries import (
    count_jobs_by_run_id,
    get_graph,
    get_jobs_by_run_id,
    get_resolution,
    get_resolution_ids_with_orphaned_jobs,
    get_resources_by_root_id,
    get_run,
    get_run_graph,
    get_stale_resolution_ids,
    save_graph,
    save_job,
    save_resolution,
)
from sematic.plugins.abstract_publisher import get_publishing_plugins
from sematic.scheduling.job_details import JobKind
from sematic.scheduling.job_scheduler import clean_jobs, schedule_resolution
from sematic.scheduling.kubernetes import cancel_job

logger = logging.getLogger(__name__)

_GARBAGE_COLLECTION_QUERIES = {
    "orphaned_jobs": get_resolution_ids_with_orphaned_jobs,
    "stale": get_stale_resolution_ids,
}


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

    payload = dict(content=get_resolution_payload(resolution))

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

    resolution, updated = _update_resolution_user(resolution=resolution, user=user)
    if updated:
        logger.debug(
            "Updated Resolution %s User to %s", resolution.root_id, resolution.user_id
        )

    logger.info(
        "Attempting to update resolution %s; status: %s; user: %s",
        resolution.root_id,
        resolution.status,
        resolution.user_id,
    )

    if not resolution.root_id == resolution_id:
        message = (
            f"Id of resolution in the payload ({resolution.root_id}) does not match "
            f"the one from the endpoint called ({resolution_id})"
        )
        logger.warning(message)
        return jsonify_error(message, HTTPStatus.BAD_REQUEST)

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

    previous_status = None
    try:
        if existing_resolution is not None:
            previous_status = existing_resolution.status
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
        # we want to log a message when the resolution is moved
        # from a non-terminal state to a terminal state.
        is_termination_update = (
            previous_status is not None
            and not ResolutionStatus[previous_status].is_terminal()  # type: ignore
        )
        if is_termination_update:
            # Note: This message can be used to extract information about pipeline
            # status for usage in dashboards. Some users may be leveraging it for
            # such purposes, so think carefully before changing/removing it.
            was_remote = (
                count_jobs_by_run_id(resolution.root_id, kind=JobKind.resolver) > 0
            )
            duration_seconds: Union[float, str] = "UNKNOWN"
            if root_run.started_at is not None:
                duration_seconds = (
                    datetime.utcnow() - root_run.started_at
                ).total_seconds()

            logger.info(
                "%s resolution %s for pipeline %s terminated with "
                "root run in state %s. The duration was %s seconds. "
                "Git dirty: %s . Git branch: '%s' . "
                "The root run had tags: %s .",
                "Remote" if was_remote else "Local",
                resolution.root_id,
                root_run.calculator_path,
                root_run.future_state,
                duration_seconds,
                getattr(resolution.git_info, "dirty", "UNKNOWN"),
                getattr(resolution.git_info, "branch", "UNKNOWN"),
                root_run.tags,
            )
        try:
            _cancel_non_terminal_runs(resolution.root_id)
        except Exception as e:
            logger.exception("Error when trying to cancel runs in resolution:", e)

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

    jobs = get_jobs_by_run_id(resolution_id, kind=JobKind.resolver)
    if len(jobs) != 0:
        return jsonify_error(
            f"Resolution {resolution_id} was already scheduled",
            status=HTTPStatus.BAD_REQUEST,
        )

    try:
        resolution, updated = _update_resolution_user(resolution=resolution, user=user)
        if updated:
            logger.debug(
                "Updated Resolution %s User to %s",
                resolution.root_id,
                resolution.user_id,
            )
            save_resolution(resolution)

        resolution, post_schedule_job = schedule_resolution(
            resolution=resolution,
            max_parallelism=max_parallelism,
            rerun_from=rerun_from,
        )

        logger.info("Scheduled resolution with job %s", post_schedule_job.identifier())
        save_resolution(resolution)
        save_job(post_schedule_job)

    except MissingSettingsError as e:
        return jsonify_error(str(e), status=HTTPStatus.BAD_REQUEST)

    except Exception as e:
        return jsonify_error(str(e), status=HTTPStatus.INTERNAL_SERVER_ERROR)

    payload = dict(content=get_resolution_payload(resolution))

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

    resolution = clone_resolution(resolution=original_resolution, root_id=root_run.id)

    resolution, updated = _update_resolution_user(resolution=resolution, user=user)
    if updated:
        logger.debug(
            "Updated resolution %s user to %s", resolution.root_id, resolution.user_id
        )
        save_resolution(resolution)

    resolution, post_schedule_job = schedule_resolution(
        resolution=resolution, rerun_from=rerun_from
    )

    save_resolution(resolution)
    save_job(post_schedule_job)

    payload = dict(content=get_resolution_payload(resolution))

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

    jobs = get_jobs_by_run_id(resolution.root_id, kind=JobKind.resolver)
    for job in jobs:
        logger.info("Canceling %s", job.identifier())
        post_cancel_job = cancel_job(job)
        save_job(post_cancel_job)

    resolution.status = ResolutionStatus.CANCELED
    save_resolution(resolution)

    _cancel_non_terminal_runs(resolution.root_id)

    broadcast_graph_update(root_id=resolution.root_id, user=user)
    broadcast_resolution_cancel(
        root_id=resolution.root_id, calculator_path=root_run.calculator_path, user=user
    )

    payload = dict(content=get_resolution_payload(resolution))

    return flask.jsonify(payload)


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
        run.future_state = FutureState.CANCELED
        run.failed_at = datetime.utcnow()

    save_graph(unfinished_runs, [], [])

    for run in unfinished_runs:
        for job in get_jobs_by_run_id(run.id):
            logger.info("Canceling %s", job.identifier())
            save_job(cancel_job(job))


def _update_resolution_user(
    resolution: Resolution, user: Optional[User]
) -> Tuple[Resolution, bool]:
    """
    Updates the Resolution's User details, returning the updated Resolution, and whether
    any changes were actually made.
    """
    var_key = str(UserSettingsVar.SEMATIC_API_KEY.value)

    if user is None:
        if resolution.user_id is None:
            return resolution, False

        resolution.user_id = None
        del resolution.settings_env_vars[var_key]
        return resolution, True

    if user.id == resolution.user_id:
        return resolution, False

    resolution.user_id = user.id
    resolution.settings_env_vars[var_key] = user.api_key

    return resolution, True


@sematic_api.route("/api/v1/resolutions", methods=["GET"])
@authenticate
def list_resolutions_endpoint(user: Optional[User]) -> flask.Response:
    """
    GET /api/v1/resolutions endpoint.

    The API endpoint to list and filter resolutions. Returns a JSON payload.

    Parameters
    ----------
    filters : Optional[str]
        Filters of the form `{"column_name": {"operator": "value"}}`. Currenrly only
        a pseudo-column with the name of "orphaned_jobs" and type bool is supported.
        Defaults to None.
    fields: Optional[List[str]]
        The fields of the run object to include in the result. If not set, all fields
        will be returned. Currently the only supported subset of fields is ["root_id"].
        The ["root_id"] subset must be used when the "orphaned_jobs" filter is used.

    Response
    --------
    current_page_url : str
        URL of the current page
    next_page_url : Optional[str]
        URL of the next page, if any, `null` otherwise
    limit : int
        Current page size. The actual number of items returned may be smaller
        if current page is last page.
    next_cursor : Optional[str]
        Cursor to obtain next page. Already included in `next_page_url`.
    after_cursor_count : int
        Number of items remain after the current cursor, i.e. including the current page.
    content : List[Dict[str, str]]
        A list of resolution JSON payloads, if the 'fields' request parameter was not set.
        If the 'fields' parameter was set to ['root_id'], returns a list of resolution
        ids. The size of the list is `limit` or less if current page is last page.
    """
    request_args = dict(flask.request.args)
    contained_extra_filters, garbage_filters = get_gc_filters(
        request_args, list(_GARBAGE_COLLECTION_QUERIES.keys())
    )
    logger.info(
        "Searching for resolutions to garbage collect with filters: %s",
        garbage_filters,
    )
    if len(garbage_filters) == 0:
        return jsonify_error(
            "Currently the only supported resolution search is with the filter "
            "'orphaned_jobs'.",
            status=HTTPStatus.BAD_REQUEST,
        )

    if contained_extra_filters or len(garbage_filters) > 1:
        return jsonify_error(
            f"Filter {garbage_filters[0]} must be used alone",
            status=HTTPStatus.BAD_REQUEST,
        )

    return list_garbage_ids(
        garbage_filters[0],
        flask.request.url,
        _GARBAGE_COLLECTION_QUERIES,
        Resolution,
        urlencode(request_args),
        id_field="root_id",
    )


@sematic_api.route("/api/v1/resolutions/<root_id>/clean_jobs", methods=["POST"])
@authenticate
def clean_orphaned_resolution_jobs_endpoint(
    user: Optional[User], root_id: str
) -> flask.Response:
    resolution = get_resolution(root_id)
    if not ResolutionStatus[resolution.status].is_terminal():  # type: ignore
        message = (
            f"Can't clean jobs of resolution {root_id} "
            f"in non-terminal state {resolution.status}."
        )
        logger.error(message)
        return jsonify_error(message, HTTPStatus.BAD_REQUEST)
    force = flask.request.args.get("force", "false").lower() == "true"
    jobs = get_jobs_by_run_id(root_id, kind=JobKind.resolver)
    state_changes = clean_jobs(jobs, force)
    return flask.jsonify(
        dict(
            content=[change.value for change in state_changes],
        )
    )


@sematic_api.route("/api/v1/resolutions/<root_id>/clean", methods=["POST"])
@authenticate
def clean_stale_resolution_endpoint(
    user: Optional[User], root_id: str
) -> flask.Response:
    resolution = get_resolution(root_id)
    root_run = get_run(root_id)

    if not FutureState[root_run.future_state].is_terminal():  # type: ignore
        return jsonify_error(
            f"Couldn't clean resolution {root_id} because its root run "
            f"is in state {root_run.future_state}",
            status=HTTPStatus.CONFLICT,
        )

    state_change = "UNMODIFIED"
    if not ResolutionStatus[resolution.status].is_terminal():  # type: ignore
        logger.warning(
            "Marking resolution %s as failed because it wasn't properly terminated.",
            root_id,
        )
        resolution.status = ResolutionStatus.FAILED
        state_change = ResolutionStatus.FAILED.value
        save_resolution(resolution)

    return flask.jsonify(
        dict(
            content=state_change,
        )
    )
