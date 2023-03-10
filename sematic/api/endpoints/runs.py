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
from sematic.api.endpoints.payloads import get_run_payload, get_runs_payload
from sematic.api.endpoints.request_parameters import (
    get_request_parameters,
    jsonify_error,
)
from sematic.db.db import db
from sematic.db.models.artifact import Artifact
from sematic.db.models.edge import Edge
from sematic.db.models.job import Job
from sematic.db.models.run import Run
from sematic.db.models.user import User
from sematic.db.queries import (
    get_external_resources_by_run_id,
    get_resolution,
    get_root_graph,
    get_run,
    get_run_graph,
    get_run_status_details,
    jobs_by_run_id,
    save_graph,
    save_job,
    save_run,
    save_run_external_resource_links,
)
from sematic.log_reader import load_log_lines
from sematic.scheduling.external_job import ExternalJob
from sematic.scheduling.job_scheduler import schedule_run, update_run_status
from sematic.scheduling.kubernetes import cancel_job
from sematic.utils.exceptions import IllegalStateTransitionError
from sematic.utils.retry import retry

logger = logging.getLogger(__name__)


class _DetectedRunRaceCondition(Exception):
    pass


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
        Filters of the form `{"column_name": {"operator": "value"}}`. Defaults to None.

    Response
    --------
    current_page_url : str
        URL of the current page
    next_page_url : Optional[str]
        URL of the next page, if any, `null` otherwise
    limit : int
        Current page size. The actual number of items returned may be inferior
        if current page is last page.
    next_cursor : Optional[str]
        Cursor to obtain next page. Already included in `next_page_url`.
    after_cursor_count : int
        Number of items remain after the current cursor, i.e. including the current page.
    content: List[Run]
        A list of run JSON payloads. The size of the list is `limit` or less if
        current page is last page.
    """
    try:
        limit, order, cursor, group_by_column, sql_predicates = get_request_parameters(
            args=flask.request.args, model=Run
        )
    except ValueError as e:
        return jsonify_error(str(e), HTTPStatus.BAD_REQUEST)

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

    resolution = get_resolution(run.root_id)
    run = schedule_run(run, resolution)
    logger.info("Scheduled run with external job: %s", run.external_jobs[-1])
    run.started_at = datetime.datetime.utcnow()

    save_run(run)

    broadcast_graph_update(root_id=run.root_id, user=user)
    save_job(Job.from_job(run.external_jobs[-1], run_id=run.id))
    broadcast_job_update(source_run_id=run.id, user=user)

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
    default_kwargs = dict(continuation_cursor=None, max_lines=100, filter_strings=None)
    kwarg_converters = dict(
        continuation_cursor=lambda v: v if v is None else str(v),
        max_lines=int,
        filter_strings=lambda v: [] if v is None else list(v),
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
    run_id: str, future_state: FutureState, jobs: List[ExternalJob]
) -> Tuple[Optional[Run], Optional[Tuple[ExternalJob, ...]]]:
    """Returns the updated run & its jobs, if they changed job status, or None
    if they haven't
    """
    new_future_state, new_external_jobs = update_run_status(future_state, jobs)
    run = None

    # we standardize to tuples, but sometimes we get lists
    if tuple(new_external_jobs) != tuple(jobs):
        run = get_run(run_id)
        run.external_jobs = new_external_jobs
        run.external_exception_metadata = new_external_jobs[-1].get_exception_metadata()
        logger.info("Updating run's external jobs: %s", new_external_jobs)

    if new_future_state != future_state:
        # why have get_run both here and in the block above about
        # external jobs? Why not just get the run outside both blocks?
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

    if new_external_jobs == jobs:
        new_external_jobs = None  # type: ignore

    return (run, new_external_jobs)


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

    db_status_dict = get_run_status_details(run_ids)
    missing_run_ids = set(run_ids).difference(db_status_dict.keys())
    if len(missing_run_ids) != 0:
        return jsonify_error(
            f"Missing runs with ids: {','.join(missing_run_ids)}", HTTPStatus.NOT_FOUND
        )

    result_list = []
    for run_id, (future_state, jobs) in db_status_dict.items():
        new_future_state_value = future_state.value
        run, new_jobs = _get_run_and_jobs_if_modified(run_id, future_state, jobs)
        if run is not None:
            new_future_state_value = run.future_state
            try:
                save_run(run)
            except IllegalStateTransitionError as e:
                raise _DetectedRunRaceCondition(
                    "Run appears to have been modified since being queried: %s", e
                )
            broadcast_graph_update(run.root_id, user=user)

        if new_jobs is not None and len(new_jobs) > 0:
            for job in new_jobs:
                save_job(Job.from_job(job, run_id=run_id))
            broadcast_job_update(source_run_id=run_id, user=user)

        result_list.append(
            dict(
                run_id=run_id,
                future_state=new_future_state_value,
            )
        )

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

    # save graph BEFORE ensuring jobs are stopped. This way
    # code that is checking on job status will be ok if it
    # sees the jobs as gone while we are going through and
    # deleting them.
    save_graph(runs, artifacts, edges)

    updated_jobs = False
    for run in runs:
        if FutureState[run.future_state].is_terminal():
            updated_jobs = True
            logger.info("Ensuring jobs for %s are stopped %s", run.id, run.future_state)
            jobs = []
            for external_job in run.external_jobs:
                canceled_job = cancel_job(external_job)
                save_job(Job.from_job(canceled_job, run_id=run.id))
                jobs.append(canceled_job)
            if len(jobs) > 0:
                broadcast_job_update(source_run_id=run.id, user=user)
            run.external_jobs = jobs

    if updated_jobs:
        save_graph(runs, [], [])

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


@sematic_api.route("/api/v1/runs/<run_id>/job_status_history", methods=["GET"])
@authenticate
def get_run_job_status_history(user: Optional[User], run_id):
    jobs = jobs_by_run_id(run_id)
    job_status_histories = [
        dict(
            job_id=job.id,
            job_kind=job.job_type.value,
            status_history=[
                status["values"] for status in job.status_history_serializations
            ],
        )
        for job in jobs
    ]
    return flask.jsonify(
        dict(
            content=job_status_histories,
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
