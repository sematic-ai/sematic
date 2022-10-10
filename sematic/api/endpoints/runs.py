"""
Module keeping all /api/v*/runs/* API endpoints.
"""

# Standard Library
import base64
import datetime
import logging
from dataclasses import asdict
from http import HTTPStatus
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlencode, urlsplit, urlunsplit

# Third-party
import flask
import flask_socketio  # type: ignore
import sqlalchemy
from sqlalchemy.orm.exc import NoResultFound

# Sematic
from sematic.api.app import sematic_api
from sematic.api.endpoints.auth import authenticate
from sematic.api.endpoints.request_parameters import (
    get_request_parameters,
    jsonify_error,
)
from sematic.db.db import db
from sematic.db.models.artifact import Artifact
from sematic.db.models.edge import Edge
from sematic.db.models.run import Run
from sematic.db.models.user import User
from sematic.db.queries import (
    get_resolution,
    get_root_graph,
    get_run,
    get_run_graph,
    get_run_status_details,
    save_graph,
    save_run,
)
from sematic.log_reader import load_log_lines
from sematic.scheduling.job_scheduler import schedule_run, update_run_status
from sematic.utils.exceptions import ExceptionMetadata
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
        maximum number of results in one page. Defaults to 20.
    cursor : Optional[str]
        pagination cursor
    group_by : Optional[str]
        value to group runs by. If none null, the endpoint will return
        a single run by unique value of the field passed in `group_by`.
    filters : Optional[str]
        filters of the form `{"column_name": {"operator": "value"}}`
        Only single filter supporter for now.

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
        Number of items remain after the current cursos, i.e. including current
        page.
    content: List[Run]
        A list of run JSON payloads. The size of the list is `limit` or less if
        current page is last page.
    """
    limit, cursor, group_by_column, sql_predicates = get_request_parameters(
        flask.request.args, Run
    )

    decoded_cursor: Optional[str] = None
    if cursor is not None:
        try:
            decoded_cursor = base64.urlsafe_b64decode(bytes(cursor, "utf-8")).decode(
                "utf-8"
            )
        except Exception:
            raise Exception("invalid cursor")

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

        query = query.order_by(sqlalchemy.desc(Run.created_at))

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

    content = [run.to_json_encodable() for run in runs]

    payload = dict(
        current_page_url=current_page_url,
        next_page_url=next_page_url,
        limit=limit,
        next_cursor=next_cursor,
        after_cursor_count=after_cursor_count,
        content=content,
    )

    return flask.jsonify(payload)


def _make_cursor(key: str) -> str:
    return base64.urlsafe_b64encode(bytes(key, "utf-8")).decode("utf-8")


@sematic_api.route("/api/v1/runs/<run_id>", methods=["GET"])
@authenticate
def get_run_endpoint(user: Optional[User], run_id: str) -> flask.Response:
    try:
        run = get_run(run_id)
    except NoResultFound:
        return jsonify_error(
            "No runs with id {}".format(repr(run_id)), HTTPStatus.NOT_FOUND
        )

    payload = dict(
        content=run.to_json_encodable(),
    )

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
    payload = dict(
        content=run.to_json_encodable(),
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


class InvalidStateTransitionError(Exception):
    pass


@sematic_api.route("/api/v1/runs/future_states", methods=["POST"])
@authenticate
@retry(_DetectedRunRaceCondition, tries=3, delay=10, jitter=1)
def update_run_status_endpoint(user: Optional[User]) -> flask.Response:
    """Update the state of runs based on external job status, and return results"""
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
        new_future_state, message, new_external_jobs = update_run_status(
            future_state, jobs
        )
        run_modified = False
        run = None
        if new_external_jobs != jobs:
            run = get_run(run_id)
            run.external_jobs = new_external_jobs
            logger.info("Updating run's external jobs: %s", new_external_jobs)
            run_modified = True
        if new_future_state != future_state:
            # why have get_run both here and in the block above about
            # external jobs? Why not just get the run outside both blocks?
            # because this endpoint gets called A LOT, and we want to
            # avoid loading the run from the DB unless we detect that something
            # has changed and we need to load it to modify. The common case will
            # be that nothing has changed and the run-reload is not needed.
            run = get_run(run_id) if run is None else run
            run_modified = True
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

            if message is not None and run.exception is None:
                run.exception = ExceptionMetadata(
                    repr=message,
                    name=InvalidStateTransitionError.__name__,
                    module=InvalidStateTransitionError.__module__,
                )

            logger.info(
                "Updating run %s from %s to %s. Message: %s",
                run_id,
                future_state,
                new_future_state,
                message,
            )
        if run_modified and run is not None:
            # note: the "is not None" is redundant but pleases mypy
            save_run(run)
        result_list.append(
            dict(
                run_id=run_id,
                future_state=new_future_state.value,
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
        runs=[run.to_json_encodable() for run in runs],
        edges=[edge.to_json_encodable() for edge in edges],
        artifacts=[artifact.to_json_encodable() for artifact in artifacts],
    )

    return flask.jsonify(payload)


@sematic_api.route("/api/v1/events/<namespace>/<event>", methods=["POST"])
@authenticate
def events(user: Optional[User], namespace: str, event: str) -> flask.Response:
    flask_socketio.emit(
        event,
        flask.request.json,
        namespace="/{}".format(namespace),
        broadcast=True,
    )
    return flask.jsonify({})


@sematic_api.route("/api/v1/graph", methods=["PUT"])
@authenticate
def save_graph_endpoint(user: Optional[User]):
    if not flask.request or not flask.request.json or "graph" not in flask.request.json:
        return jsonify_error(
            "Please provide a graph payload in JSON format.",
            HTTPStatus.BAD_REQUEST,
        )

    graph = flask.request.json["graph"]

    runs = [Run.from_json_encodable(run) for run in graph["runs"]]
    for run in runs:
        logger.info("Graph update, run %s is in state %s", run.id, run.future_state)
    artifacts = [
        Artifact.from_json_encodable(artifact) for artifact in graph["artifacts"]
    ]
    edges = [Edge.from_json_encodable(edge) for edge in graph["edges"]]

    # try:
    save_graph(runs, artifacts, edges)
    # except Exception as e:
    #    return jsonify_error(str(e), HTTPStatus.INTERNAL_SERVER_ERROR)

    return flask.jsonify({})
