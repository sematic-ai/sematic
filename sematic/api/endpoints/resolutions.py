"""
Module keeping all /api/v*/runs/* API endpoints.
"""

# Standard Library
import logging
from datetime import datetime
from http import HTTPStatus
from typing import Callable, Dict, List, Optional, Tuple, Union
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
from sematic.db.models.job import Job
from sematic.db.models.resolution import InvalidResolution, Resolution, ResolutionStatus
from sematic.db.models.run import Run
from sematic.db.models.user import User
from sematic.db.queries import (
    count_jobs_by_run_id,
    get_active_resolution_ids,
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
from sematic.graph import RerunMode
from sematic.plugins.abstract_publisher import get_publishing_plugins
from sematic.scheduling.job_details import JobKind
from sematic.scheduling.job_scheduler import (
    StateNotSchedulable,
    clean_jobs,
    refresh_jobs,
    schedule_resolution,
)
from sematic.scheduling.kubernetes import cancel_job
from sematic.utils.exceptions import ExceptionMetadata


logger = logging.getLogger(__name__)

_GARBAGE_COLLECTION_QUERIES: Dict[str, Callable[[], List[str]]] = {
    "orphaned_jobs": get_resolution_ids_with_orphaned_jobs,
    "stale": get_stale_resolution_ids,
    # Note: This is replaced below once it's defined.
    # Unlike the first two, which require only looking in the
    # server's metadata, to identify zombies we need to check the actual
    # k8s cluster to see if the runner pod is still around.
    "zombie": lambda: [],
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
                root_run.function_path,
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

    try:
        jobs = get_jobs_by_run_id(resolution.root_id, kind=JobKind.resolver)
        updated_jobs = refresh_jobs(jobs)
        for job in updated_jobs:
            save_job(job)
    except Exception:
        logger.exception("Error updating jobs for resolution %s", resolution.id)

    return flask.jsonify({})


@sematic_api.route("/api/v1/resolutions/<resolution_id>/schedule", methods=["POST"])
@authenticate
def schedule_resolution_endpoint(
    user: Optional[User], resolution_id: str
) -> flask.Response:
    resolution = get_resolution(resolution_id)

    max_parallelism, rerun_from, rerun_mode = None, None, None

    if flask.request.json:
        if "max_parallelism" in flask.request.json:
            max_parallelism = flask.request.json["max_parallelism"]

        if "rerun_from" in flask.request.json:
            rerun_from = flask.request.json["rerun_from"]

        if "rerun_mode" in flask.request.json:
            rerun_mode = RerunMode[flask.request.json["rerun_mode"]]

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
            rerun_mode=rerun_mode,
        )

        logger.info("Scheduled resolution with job %s", post_schedule_job.identifier())
        save_resolution(resolution)
        save_job(post_schedule_job)

    except MissingSettingsError as e:
        return jsonify_error(str(e), status=HTTPStatus.BAD_REQUEST)

    except StateNotSchedulable as e:
        root_run = get_run(resolution_id)
        root_run.exception_metadata = ExceptionMetadata(
            repr=f"Failed because the runner job could not be scheduled: {e}",
            name=StateNotSchedulable.__name__,
            module=StateNotSchedulable.__module__,
            ancestors=ExceptionMetadata.ancestors_from_exception(StateNotSchedulable),
        )
        root_run.failed_at = datetime.utcnow()
        root_run.future_state = FutureState.FAILED
        save_graph(runs=[root_run], artifacts=[], edges=[])
        resolution.status = ResolutionStatus.FAILED
        save_resolution(resolution)
        logger.exception("Exception saved for resolution %s", root_run.id)
        broadcast_pipeline_update(function_path=root_run.function_path, user=user)
        return jsonify_error(str(e), status=HTTPStatus.INTERNAL_SERVER_ERROR)
    except Exception as e:
        return jsonify_error(str(e), status=HTTPStatus.INTERNAL_SERVER_ERROR)

    payload = dict(content=get_resolution_payload(resolution))

    return flask.jsonify(payload)


@sematic_api.route("/api/v1/resolutions/<resolution_id>/rerun", methods=["POST"])
@authenticate
def rerun_resolution_endpoint(user: Optional[User], resolution_id: str) -> flask.Response:
    original_resolution = get_resolution(resolution_id)

    if original_resolution.container_image_uri is None:
        return jsonify_error(
            (
                f"Resolution {original_resolution.root_id} cannot be re-run: "
                f"it was initially resolved locally, and therefore "
                f"no container image was built"
            ),
            HTTPStatus.BAD_REQUEST,
        )

    rerun_from = None
    if flask.request.json and "rerun_from" in flask.request.json:
        rerun_from = flask.request.json["rerun_from"]
        logger.debug("Rerunning from: %s", rerun_from)

    artifacts_override = {}
    if flask.request.json and "artifacts" in flask.request.json:
        artifacts_override = flask.request.json["artifacts"]
        if not isinstance(artifacts_override, dict):
            return jsonify_error(
                f"Malformed parameter `artifacts`: {artifacts_override}",
                HTTPStatus.BAD_REQUEST,
            )
        logger.debug("Rerunning with artifacts override: %s", artifacts_override)

    if rerun_from is not None and len(artifacts_override):
        # specifying `rerun_from` invalidates a subgraph (in the general case)
        # specifying `artifacts` results in the entire resolution being invalidated,
        # effectively being equivalent to  always passing `rerun_from` with the root run
        # id, so no other value can be supported
        return jsonify_error(
            "Cannot specify both `rerun_from` and `artifacts` when rerunning a pipeline.",
            HTTPStatus.BAD_REQUEST,
        )

    original_runs, _, original_edges = get_run_graph(run_id=original_resolution.root_id)
    original_root_run = original_runs[0]

    root_run, edges = clone_root_run(
        run=original_root_run,
        edges=original_edges,
        artifacts_override=artifacts_override,
    )
    logger.info("Cloning %s to %s", resolution_id, root_run.id)

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

    try:
        logger.info("Scheduling resolution %s", root_run.id)
        resolution, post_schedule_job = schedule_resolution(
            resolution=resolution, rerun_from=rerun_from
        )

    except StateNotSchedulable as e:
        logger.exception("Exception scheduling resolution %s", root_run.id)
        root_run.exception_metadata = ExceptionMetadata(
            repr=f"Failed because the runner job could not be scheduled: {e}",
            name=StateNotSchedulable.__name__,
            module=StateNotSchedulable.__module__,
            ancestors=ExceptionMetadata.ancestors_from_exception(StateNotSchedulable),
        )
        root_run.failed_at = datetime.utcnow()
        root_run.future_state = FutureState.FAILED
        save_graph(runs=[root_run], artifacts=[], edges=[])
        resolution.status = ResolutionStatus.FAILED
        save_resolution(resolution)
        logger.exception("Exception saved for resolution %s", root_run.id)
        broadcast_pipeline_update(function_path=root_run.function_path, user=user)
        return jsonify_error(str(e), status=HTTPStatus.INTERNAL_SERVER_ERROR)

    except Exception as e:
        return jsonify_error(str(e), status=HTTPStatus.INTERNAL_SERVER_ERROR)

    save_resolution(resolution)
    save_job(post_schedule_job)

    payload = dict(content=get_resolution_payload(resolution))

    broadcast_pipeline_update(function_path=root_run.function_path, user=user)

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
        root_id=resolution.root_id, function_path=root_run.function_path, user=user
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
        if resolution.settings_env_vars is not None:
            del resolution.settings_env_vars[var_key]

        return resolution, True

    if user.id == resolution.user_id:
        return resolution, False

    resolution.user_id = user.id
    if resolution.settings_env_vars is None:
        resolution.settings_env_vars = {}
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
def clean_stale_resolution_endpoint(user: Optional[User], root_id: str) -> flask.Response:
    resolution = get_resolution(root_id)
    root_run = get_run(root_id)
    logger.info(
        "Cleaning resolution %s with status %s and root run state %s",
        root_id,
        resolution.status,
        root_run.future_state,
    )

    resolution_jobs = get_jobs_by_run_id(root_id, kind=JobKind.resolver)
    refreshed_resolution_jobs = refresh_jobs(resolution_jobs)
    has_active_jobs = any(
        job.get_latest_status().is_active() for job in refreshed_resolution_jobs
    )
    metadata_shows_running = not ResolutionStatus[
        resolution.status  # type: ignore
    ].is_terminal()
    is_zombie = metadata_shows_running and not has_active_jobs

    root_run_running = not FutureState[
        root_run.future_state  # type: ignore
    ].is_terminal()

    # If the root run is running, we don't want to risk stopping useful
    # work. But zombies already are known to not have any jobs for themselves
    # or their runs (but due to the dead resolver, they might have left runs in
    # non-terminal states).
    if root_run_running and not is_zombie:  # type: ignore
        return jsonify_error(
            f"Couldn't clean resolution {root_id} because its root run "
            f"is in state {root_run.future_state}, and it still has active jobs.",
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

    for old_job, new_job in zip(resolution_jobs, refreshed_resolution_jobs):
        if (
            old_job.get_latest_status().is_active()
            and not new_job.get_latest_status().is_active()
        ):
            save_job(new_job)

    return flask.jsonify(
        dict(
            content=state_change,
        )
    )


def _get_zombie_resolution_ids() -> List[str]:
    """Get ids of resolutions with no jobs still alive, but which appear non-terminal"""
    active_ids = get_active_resolution_ids()
    zombie_ids = []
    for active_resolution_id in active_ids:
        try:
            original_jobs = get_jobs_by_run_id(
                active_resolution_id, kind=JobKind.resolver
            )
            jobs = refresh_jobs(original_jobs)
            active_jobs = [job for job in jobs if job.get_latest_status().is_active()]
            if len(active_jobs) > 0:
                logger.info(
                    "Resolution has active job %s: %s",
                    active_jobs[0].name,
                    active_jobs[0].details,
                )
                continue
            logger.warning(
                "Resolution %s has no active job; likely a zombie",
                active_resolution_id,
            )
            run_jobs = _get_active_jobs_for_resolution_id(active_resolution_id)
            refreshed_jobs = refresh_jobs(run_jobs)
            active_run_jobs = [
                job for job in refreshed_jobs if job.get_latest_status().is_active()
            ]
            if len(active_run_jobs) > 0:
                # Why not consider it to be a zombie when the resolution has
                # no job but a run does? Because (a) the run might still be doing
                # useful work that we want it to complete (ex: to view, or for reruns)
                # and (b) it's possible (though not likely) that we happened to catch
                # the resolution at a moment when its pod was evicted, and it might
                # recover with a reschedule. Making sure we only consider it a zombie
                # if it still has runs with active jobs avoids this potential
                # mis-identification.
                logger.warning(
                    "Resolution may be defunct but a run job is still active: %s",
                    active_run_jobs[0].name,
                )
                continue
            else:
                logger.warning(
                    "Jobs for runs of resolution with id %s are no longer active",
                    active_resolution_id,
                )

            zombie_ids.append(active_resolution_id)
        except Exception:
            logger.exception(
                "Error refreshing jobs for resolution %s", active_resolution_id
            )
    return zombie_ids


def _get_active_jobs_for_resolution_id(resolution_id: str) -> List[Job]:
    runs = get_graph(Run.root_id == resolution_id)[0]
    active_run_jobs: List[Job] = []
    for run in runs:
        if FutureState[run.future_state] != FutureState.SCHEDULED:  # type: ignore
            continue
        run_jobs = get_jobs_by_run_id(run.id, kind=JobKind.run)
        active_run_jobs.extend(
            job for job in run_jobs if job.get_latest_status().is_active()
        )
    return active_run_jobs


_GARBAGE_COLLECTION_QUERIES["zombie"] = _get_zombie_resolution_ids
