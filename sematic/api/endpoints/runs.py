"""
Module keeping all /api/v*/runs/* API endpoints.
"""

# Standard Library
import base64
import datetime
import logging
from dataclasses import asdict
from http import HTTPStatus
from typing import Any, Dict, List, Optional, Tuple, Union
from urllib.parse import urlencode, urlsplit, urlunsplit

# Third-party
import flask
import sqlalchemy
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql.elements import BooleanClauseList

# Sematic
from sematic.abstract_future import FutureState
from sematic.api.app import sematic_api
from sematic.api.endpoints.auth import authenticate
from sematic.api.endpoints.events import broadcast_graph_update, broadcast_job_update
from sematic.api.endpoints.metrics import MetricEvent, save_event_metrics
from sematic.api.endpoints.payloads import get_run_payload, get_runs_payload
from sematic.api.endpoints.request_parameters import (
    get_gc_filters,
    get_request_parameters,
    jsonify_error,
    list_garbage_ids,
)
from sematic.db.db import db
from sematic.db.models.artifact import Artifact
from sematic.db.models.edge import Edge
from sematic.db.models.job import Job
from sematic.db.models.resolution import ResolutionStatus
from sematic.db.models.run import Run
from sematic.db.models.user import User
from sematic.db.queries import (
    get_basic_pipeline_metrics,
    get_existing_run_ids,
    get_external_resources_by_run_id,
    get_jobs_by_run_id,
    get_orphaned_run_ids,
    get_resolution,
    get_root_graph,
    get_run,
    get_run_graph,
    get_run_ids_with_orphaned_jobs,
    get_run_status_details,
    save_graph,
    save_job,
    save_run,
    save_run_external_resource_links,
)
from sematic.log_reader import load_log_lines
from sematic.scheduling.job_scheduler import clean_jobs, schedule_run, update_run_status
from sematic.scheduling.kubernetes import cancel_job
from sematic.utils.exceptions import ExceptionMetadata, IllegalStateTransitionError
from sematic.utils.retry import retry

logger = logging.getLogger(__name__)


class _DetectedRunRaceCondition(Exception):
    pass


_GARBAGE_COLLECTION_QUERIES = {
    "orphaned_jobs": get_run_ids_with_orphaned_jobs,
    "orphaned": get_orphaned_run_ids,
}


@sematic_api.route("/api/v1/runs", methods=["GET"])
@authenticate
def list_runs_endpoint(user: Optional[User]) -> flask.Response:
    """
    GET /api/v1/runs endpoint.

    The API endpoint to list and filter runs. Returns a JSON payload.

    Parameters
    ----------
    limit : Optional[int]
        Maximum number of results in one page. Defaults to 20.
    order : Optional[Literal["asc", "desc"]]
        Direction to order the `created_at` column by. By default, will sort in
        descending order.
    cursor : Optional[str]
        The pagination cursor. Defaults to None.
    group_by : Optional[str]
        Value to group runs by. If not None, the endpoint will return
        a single run by unique value of the field passed in `group_by`.
    filters : Optional[str]
        Filters of the form `{"column_name": {"operator": "value"}}`. A pseudo-column
        name of "orphaned_jobs" and type bool is supported. Defaults to None.
    fields: Optional[List[str]]
        The fields of the run object to include in the result. If not set, all fields
        will be returned. Currently the only supported subset of fields is ["id"]. The
        ["id"] subset must be used when the "orphaned_jobs" filter is used. Defaults to
        None.

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
    content : List[Run]
        A list of run JSON payloads, if the 'fields' request parameter was not set.
        If the 'fields' parameter was set to ['id'], returns a list of run ids. The
        size of the list is `limit` or less if current page is last page.
    """
    request_args = dict(flask.request.args)
    contained_extra_filters, garbage_filters = get_gc_filters(
        request_args, list(_GARBAGE_COLLECTION_QUERIES.keys())
    )
    if len(garbage_filters) == 0:
        return _standard_list_runs(request_args)

    logger.info(
        "Searching for runs to garbage collect with filters: %s", garbage_filters
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
        Run,
        urlencode(request_args),
    )


def _standard_list_runs(args: Dict[str, str]) -> flask.Response:
    try:
        parameters = get_request_parameters(args=args, model=Run)
    except ValueError as e:
        return jsonify_error(str(e), HTTPStatus.BAD_REQUEST)

    if parameters.fields is not None and parameters.fields != ["id"]:
        return jsonify_error(
            "'fields' must be either `None` or `['id']`",
            HTTPStatus.BAD_REQUEST,
        )

    limit, order, cursor, group_by_column, sql_predicates = (
        parameters.limit,
        parameters.order,
        parameters.cursor,
        parameters.group_by,
        parameters.filters,
    )

    decoded_cursor: Optional[str] = None
    if cursor is not None:
        try:
            decoded_cursor = base64.urlsafe_b64decode(bytes(cursor, "utf-8")).decode(
                "utf-8"
            )
        except BaseException:
            return jsonify_error("invalid value for 'cursor'", HTTPStatus.BAD_REQUEST)

    with db().get_session() as session:
        query = session.query(Run)

        if group_by_column is not None:
            sub_query = (
                session.query(
                    group_by_column,
                    # TODO: Parametrize this part as well
                    sqlalchemy.sql.expression.func.max(Run.created_at).label(
                        "max_created_at"
                    ),
                )
                .group_by(group_by_column)
                .subquery("grouped_runs")
            )

            query = query.join(
                sub_query,
                sqlalchemy.and_(
                    group_by_column == getattr(sub_query.c, group_by_column.name),
                    Run.created_at == sub_query.c.max_created_at,
                ),
            )

        if sql_predicates is not None:
            query = query.filter(sql_predicates)

        search_string = flask.request.args.get("search")
        if search_string is not None:
            search_predicates = _generate_search_predicate(search_string)
            query = query.filter(search_predicates)

        if decoded_cursor is not None:
            query = query.filter(
                sqlalchemy.text(
                    "(runs.created_at || '_' || runs.id) < '{}'".format(
                        # PostgreSQL
                        # "CONCAT(runs.created_at, '_', runs.id) < '{}'".format(
                        decoded_cursor
                    )
                )
            )

        query = query.order_by(order(Run.created_at))

        runs: List[Run] = query.limit(limit).all()
        after_cursor_count: int = query.count()

    current_url_params: Dict[str, str] = dict(limit=str(limit))
    if cursor is not None:
        current_url_params["cursor"] = cursor

    scheme, netloc, path, _, fragment = urlsplit(flask.request.url)
    current_page_url = urlunsplit(
        (scheme, netloc, path, urlencode(current_url_params), fragment)
    )

    next_page_url: Optional[str] = None
    next_cursor: Optional[str] = None

    if runs and after_cursor_count > limit:
        next_url_params: Dict[str, str] = dict(limit=str(limit))
        next_cursor = _make_cursor("{}_{}".format(runs[-1].created_at, runs[-1].id))
        next_url_params["cursor"] = next_cursor
        next_page_url = urlunsplit(
            (scheme, netloc, path, urlencode(next_url_params), fragment)
        )

    content = get_runs_payload(runs)
    if parameters.fields == ["id"]:
        # TODO: it would be better to push this field subsetting
        # down to the DB query level, but for now we'll do it here.
        content = [{"id": run["id"] for run in content}]

    payload = dict(
        current_page_url=current_page_url,
        next_page_url=next_page_url,
        limit=limit,
        next_cursor=next_cursor,
        after_cursor_count=after_cursor_count,
        content=get_runs_payload(runs),
    )

    return flask.jsonify(payload)


def _make_cursor(key: str) -> str:
    return base64.urlsafe_b64encode(bytes(key, "utf-8")).decode("utf-8")


def _generate_search_predicate(
    search_string: str,
) -> BooleanClauseList:
    return sqlalchemy.or_(
        Run.name.ilike(f"%{search_string}%"),
        Run.calculator_path.ilike(f"%{search_string}%"),
        Run.description.ilike(f"%{search_string}%"),
        Run.id.ilike(f"%{search_string}%"),
        Run.tags.ilike(f"%{search_string}%"),
    )


@sematic_api.route("/api/v1/runs/<run_id>", methods=["GET"])
@authenticate
def get_run_endpoint(user: Optional[User], run_id: str) -> flask.Response:
    try:
        run = get_run(run_id)
    except NoResultFound:
        return jsonify_error(
            "No runs with id {}".format(repr(run_id)), HTTPStatus.NOT_FOUND
        )

    payload = dict(content=get_run_payload(run))

    return flask.jsonify(payload)


@sematic_api.route("/api/v1/runs/<run_id>/schedule", methods=["POST"])
@authenticate
def schedule_run_endpoint(user: Optional[User], run_id: str) -> flask.Response:
    """Schedule the run for execution on external compute, like k8s."""
    try:
        run = get_run(run_id)
    except NoResultFound:
        return jsonify_error(
            "No runs with id {}".format(repr(run_id)), HTTPStatus.NOT_FOUND
        )
    jobs = get_jobs_by_run_id(run_id)

    resolution = get_resolution(run.root_id)
    run, post_schedule_jobs = schedule_run(run, resolution, jobs)
    logger.info("Scheduled run with job: %s", post_schedule_jobs[-1])
    run.started_at = datetime.datetime.utcnow()

    save_run(run)

    for job in post_schedule_jobs:
        save_job(job)
    broadcast_job_update(run_id, user)

    broadcast_graph_update(root_id=run.root_id, user=user)

    payload = dict(
        content=get_run_payload(run),
    )
    return flask.jsonify(payload)


@sematic_api.route("/api/v1/runs/<run_id>/logs", methods=["GET"])
@authenticate
def get_logs_endpoint(user: Optional[User], run_id: str) -> flask.Response:
    """Get portions of the logs for the run if possible"""

    kwarg_overrides: Dict[str, Union[str, List[str]]] = dict(flask.request.args)
    if "filter_string" in kwarg_overrides:
        filter_string: str = kwarg_overrides["filter_string"]  # type: ignore
        kwarg_overrides["filter_strings"] = [filter_string]
    default_kwargs = dict(
        forward_cursor_token=None,
        reverse_cursor_token=None,
        max_lines=100,
        filter_strings=None,
        reverse=False,
    )
    kwarg_converters = dict(
        forward_cursor_token=lambda v: v if v is None else str(v),
        reverse_cursor_token=lambda v: v if v is None else str(v),
        max_lines=int,
        filter_strings=lambda v: [] if v is None else list(v),
        reverse=lambda v: v if isinstance(v, bool) else v.lower() == "true",
    )
    kwargs = {
        k: kwarg_converters[k](kwarg_overrides.get(k, default_v))  # type: ignore
        for k, default_v in default_kwargs.items()
    }

    result = load_log_lines(
        run_id=run_id,
        **kwargs,  # type: ignore
    )

    payload = dict(content=asdict(result))
    return flask.jsonify(payload)


def _get_run_and_jobs_if_modified(
    run_id: str, future_state: FutureState, jobs: List[Job]
) -> Tuple[Optional[Run], List[Job]]:
    """Returns updated run and jobs.

    Parameters
    ----------
    run_id:
        The id of the run to get updates for.
    future_state:
        The state of the run before checking against the jobs.
    jobs:
        The jobs to update.

    Returns
    -------
    A tuple where the first element is the updated run, if the run has been modified.
    If the run has not been modified, the first element will be None. The second element
    is a list of the jobs after update.
    """
    new_future_state, updated_jobs = update_run_status(future_state, jobs)
    run = None

    # we standardize to tuples, but sometimes we get lists
    if tuple(updated_jobs) != tuple(jobs):
        run = get_run(run_id)

        # We want exception metadata if it is present while the run is still
        # active, or if it has ended in a failure state. If the run has ended
        # in a non-failure state, we don't care about exception metadata from
        # the job, because it may just be something non-standard in job cleanup
        # that doesn't actually impact the outcome of the run.
        if (
            new_future_state not in FutureState.terminal_states()
            or new_future_state in FutureState.failure_terminal_states()
        ):
            run.external_exception_metadata = updated_jobs[
                -1
            ].details.get_exception_metadata()
        logger.info("Updating run's jobs: %s", updated_jobs)

    if new_future_state != future_state:
        # why have get_run both here and in the block above about
        # jobs? Why not just get the run outside both blocks?
        # because this endpoint gets called A LOT, and we want to
        # avoid loading the run from the DB unless we detect that something
        # has changed, and we need to load it to modify. The common case will
        # be that nothing has changed and the run-reload is not needed.
        run = get_run(run_id) if run is None else run

        if (
            run.future_state != future_state.value
            and run.future_state != new_future_state.value
        ):
            # future_state was pulled from the run right before we
            # started doing our updates. The server logic to this
            # point hasn't saved any status updates. The run status
            # must have been changed by a call from the worker or
            # resolver in the interim.
            raise _DetectedRunRaceCondition(
                f"Run {run_id} was changed from {future_state} to "
                f"{run.future_state} out of band of the server. The "
                f"server wanted to update the run to {new_future_state}"
            )
        run.future_state = new_future_state

        msg = (
            run.external_exception_metadata.repr
            if run.external_exception_metadata
            else None
        )
        logger.info(
            "Updating run %s from %s to %s. Message: %s",
            run_id,
            future_state,
            new_future_state,
            msg,
        )

    return run, list(updated_jobs)


@sematic_api.route("/api/v1/runs/future_states", methods=["POST"])
@authenticate
@retry(_DetectedRunRaceCondition, tries=3, delay=10, jitter=1)
def update_run_status_endpoint(user: Optional[User]) -> flask.Response:
    """Update the state of runs based on external job status, and return results."""
    input_payload: Dict[str, Any] = flask.request.json  # type: ignore
    if "run_ids" not in input_payload:
        return jsonify_error(
            "Call did not contain json with a 'run_ids' key", HTTPStatus.BAD_REQUEST
        )
    run_ids = input_payload["run_ids"]
    logger.info("Updating state for runs: %s", run_ids)

    db_status_dict = get_run_status_details(run_ids)
    missing_run_ids = set(run_ids).difference(db_status_dict.keys())
    if len(missing_run_ids) != 0:
        return jsonify_error(
            f"Missing runs with ids: {','.join(missing_run_ids)}", HTTPStatus.NOT_FOUND
        )

    result_list = []
    modified_root_runs = set()
    state_changed_runs = []
    for run_id, (future_state, jobs) in db_status_dict.items():
        new_future_state_value = future_state.value
        run, updated_jobs = _get_run_and_jobs_if_modified(run_id, future_state, jobs)
        if run is not None:
            modified_root_runs.add(run.root_id)
            new_future_state_value = run.future_state
            try:
                save_run(run)
            except IllegalStateTransitionError as e:
                raise _DetectedRunRaceCondition(
                    "Run appears to have been modified since being queried: %s", e
                )
            state_changed_runs.append(run)

        for original_job, updated_job in zip(jobs, updated_jobs or []):
            if original_job.latest_status != updated_job.latest_status:
                save_job(updated_job)
                broadcast_job_update(run_id=run_id, user=user)

        result_list.append(
            dict(
                run_id=run_id,
                future_state=new_future_state_value,
            )
        )

    for root_id in modified_root_runs:
        # modified_root_runs will contain only
        # 0 or 1 root id, unless the caller asked
        # for updates about runs in multiple
        # resolutions at once.

        # Done outside the for loop over db_status_dict.items()
        # to minimize broadcasts for high fan-out pipelines where
        # many runs from one root pipeline may happen at once.
        broadcast_graph_update(root_id, user=user)

    save_event_metrics(MetricEvent.run_state_changed, state_changed_runs, user)

    payload = dict(
        content=result_list,
    )
    return flask.jsonify(payload)


@sematic_api.route("/api/v1/runs/<run_id>/graph", methods=["GET"])
@authenticate
def get_run_graph_endpoint(user: Optional[User], run_id: str) -> flask.Response:
    """
    Retrieve graph objects for run with id `run_id`.

    This will return the run's direct graph, meaning
    only edges directly connected to it, and their corresponding artifacts.

    Request
    -------
    root: Optional[bool]
        Whether to get the entire graph, or the direct graph, meaning only the edges
        directly connected to it, and their corresponding artifacts.

    Response
    --------
    run_id: str
        ID passed in request
    runs: List[Run]
        Unique runs in the graph
    edges: List[Edge]
        Unique edges in the graph
    artifacts: List[Artifact]
        Unique artifacts in the graph
    """
    root = bool(int(flask.request.args.get("root", "0")))

    get_graph_fn = get_root_graph if root else get_run_graph

    runs, artifacts, edges = get_graph_fn(run_id)
    payload = dict(
        run_id=run_id,
        runs=get_runs_payload(runs),
        edges=[edge.to_json_encodable() for edge in edges],
        artifacts=[artifact.to_json_encodable() for artifact in artifacts],
    )

    return flask.jsonify(payload)


@sematic_api.route("/api/v1/graph", methods=["PUT"])
@authenticate
def save_graph_endpoint(user: Optional[User]):
    if not flask.request or not flask.request.json or "graph" not in flask.request.json:
        return jsonify_error(
            "Please provide a graph payload in JSON format.",
            HTTPStatus.BAD_REQUEST,
        )

    graph = flask.request.json["graph"]

    artifacts = [
        Artifact.from_json_encodable(artifact) for artifact in graph["artifacts"]
    ]

    edges = [Edge.from_json_encodable(edge) for edge in graph["edges"]]

    runs = [Run.from_json_encodable(run) for run in graph["runs"]]

    for run in runs:
        logger.info("Graph update, run %s is in state %s", run.id, run.future_state)
        if user is not None:
            run.user_id = user.id

    run_ids = [run.id for run in runs]
    existing_run_ids = get_existing_run_ids(run_ids)
    new_runs = [run for run in runs if run.id not in existing_run_ids]

    # save graph BEFORE ensuring jobs are stopped. This way
    # code that is checking on job status will be ok if it
    # sees the jobs as gone while we are going through and
    # deleting them.
    save_graph(runs, artifacts, edges)

    if len(new_runs) > 0:
        save_event_metrics(MetricEvent.run_created, new_runs, user)

    for run in runs:
        if FutureState[run.future_state].is_terminal():
            logger.info("Ensuring jobs for %s are stopped %s", run.id, run.future_state)
            for job in get_jobs_by_run_id(run.id):
                canceled_job = cancel_job(job)
                save_job(canceled_job)
            broadcast_job_update(run_id=run.id, user=user)

    return flask.jsonify({})


@sematic_api.route("/api/v1/runs/<run_id>/external_resources", methods=["GET"])
@authenticate
def get_run_external_resources(user: Optional[User], run_id):
    external_resources = get_external_resources_by_run_id(run_id)

    return flask.jsonify(
        dict(
            content=[
                external_resource.to_json_encodable()
                for external_resource in external_resources
            ],
        )
    )


@sematic_api.route("/api/v1/runs/<run_id>/external_resources", methods=["POST"])
@authenticate
def link_resource_endpoint(user: Optional[User], run_id: str) -> flask.Response:
    if (
        not flask.request
        or not flask.request.json
        or "external_resource_ids" not in flask.request.json
    ):
        return jsonify_error(
            "Please provide an external_resource_id payload with the request",
            HTTPStatus.BAD_REQUEST,
        )
    external_resource_ids = flask.request.json["external_resource_ids"]
    save_run_external_resource_links(resource_ids=external_resource_ids, run_id=run_id)
    return flask.jsonify({})


@sematic_api.route("/api/v1/runs/<run_id>/metrics", methods=["GET"])
@authenticate
def run_metrics_endpoint(user: Optional[User], run_id: str) -> flask.Response:
    run = get_run(run_id)
    pipeline_metrics = get_basic_pipeline_metrics(run.calculator_path)
    return flask.jsonify(dict(content=asdict(pipeline_metrics)))


# No "write" endpoint is needed; the server will be writing to the job
# table in response to queries that ask the server to update run state
# (rather than a client posting a job to the server).
@sematic_api.route("/api/v1/runs/<run_id>/jobs", methods=["GET"])
@authenticate
def get_run_jobs(user: Optional[User], run_id: str) -> flask.Response:
    jobs = [job.to_json_encodable() for job in get_jobs_by_run_id(run_id=run_id)]
    return flask.jsonify(
        dict(
            content=jobs,
        )
    )


@sematic_api.route("/api/v1/runs/<run_id>/clean", methods=["POST"])
@authenticate
def clean_orphaned_run_endpoint(user: Optional[User], run_id: str) -> flask.Response:
    run = get_run(run_id)
    resolution = get_resolution(run.root_id)
    if not ResolutionStatus[resolution.status].is_terminal():  # type: ignore
        return jsonify_error(
            f"The resolution for run {run_id} has not terminated "
            f"(has status: {resolution.status}).",
            status=HTTPStatus.CONFLICT,
        )
    state_change = "UNMODIFIED"

    if not FutureState[run.future_state].is_terminal():  # type: ignore
        state_change = FutureState.FAILED.value

        if run.future_state == FutureState.CREATED.value:
            run.future_state = FutureState.CANCELED
            run.ended_at = datetime.datetime.utcnow()
            state_change = FutureState.CANCELED.value
        elif FutureState.is_allowed_transition(run.future_state, FutureState.FAILED):
            run.future_state = FutureState.FAILED
            run.failed_at = datetime.datetime.utcnow()
        else:
            run.future_state = FutureState.NESTED_FAILED
            run.failed_at = datetime.datetime.utcnow()
        if run.exception_metadata is None:
            run.exception_metadata = ExceptionMetadata.from_exception(
                RuntimeError(
                    "Run was still alive despite the resolution being terminated. "
                    "Run was forced to fail."
                ),
            )
        logger.warning(
            "Marking run %s as failed because it was not terminated with its resolution.",
            run.id,
        )
        save_run(run)

    return flask.jsonify(
        dict(
            content=state_change,
        )
    )


@sematic_api.route("/api/v1/runs/<run_id>/clean_jobs", methods=["POST"])
@authenticate
def clean_orphaned_jobs_endpoint(user: Optional[User], run_id: str) -> flask.Response:
    run = get_run(run_id)
    if not FutureState[run.future_state].is_terminal():  # type: ignore
        message = (
            f"Can't clean jobs of run {run_id} "
            f"in non-terminal state {run.future_state}."
        )
        return jsonify_error(message, HTTPStatus.BAD_REQUEST)
    force = flask.request.args.get("force", "false").lower() == "true"
    jobs = get_jobs_by_run_id(run_id)
    state_changes = clean_jobs(jobs, force)
    broadcast_job_update(run_id, user)
    return flask.jsonify(
        dict(
            content=[change.value for change in state_changes],
        )
    )
