"""
Module keeping all /api/v*/runs/* API endpoints.
"""

# Standard library
import base64
import json
import typing
from urllib.parse import urlunsplit, urlencode, urlsplit

# Third-party
import sqlalchemy
import flask
from sqlalchemy.sql.elements import BinaryExpression

# Glow
from glow.api.app import glow_api
from glow.db.db import db
from glow.db.models.run import Run


# Default page size for run list
_DEFAULT_LIMIT = 20


_COLUMN_MAPPING: typing.Dict[str, sqlalchemy.Column] = {
    column.name: column for column in Run.__table__.columns
}


def _get_request_parameters(
    args: typing.Dict[str, str]
) -> typing.Tuple[
    int, typing.Optional[str], typing.Optional[str], typing.List[BinaryExpression]
]:
    """
    Extract, validate, and format query parameters.

    Parameters
    ----------
    args : Dict[str, str]
        request argument as returned by `flask.request.args`.

    Returns
    Tuple[int, Optional[str], Optional[str], List[BinaryExpression]]
        limit, custor, group_by, filters
    """
    limit: int = int(args.get("limit", _DEFAULT_LIMIT))
    if limit < 1:
        raise Exception("limit must be greater than 0")

    def _none_if_empty(name: str) -> typing.Optional[str]:
        value = args.get(name)
        if value is not None and len(value) == 0:
            value = None

        return value

    cursor = _none_if_empty("cursor")

    group_by = _none_if_empty("group_by")

    if group_by is not None and group_by not in _COLUMN_MAPPING:
        raise ValueError("Unsupported group_by value {}".format(repr(group_by)))

    filters_json: str = args.get("filters", "{}")
    filters: typing.Dict[str, typing.Any] = {}
    try:
        filters = json.loads(filters_json)
    except Exception as e:
        raise Exception("Malformed filters: {}, error: {}".format(filters_json, e))

    sql_predicates = _get_sql_predicates(filters)

    return limit, cursor, group_by, sql_predicates


def _get_sql_predicates(
    filters: typing.Dict[str, typing.Dict[str, typing.Any]]
) -> typing.List[BinaryExpression]:
    """
    Basic support for a single filter predicate.

    filters are of the form:
    ```
    {"column_name": {"operator": "value"}}
    ```
    """
    sql_predicates: typing.List[BinaryExpression] = []

    if len(filters) == 0:
        return sql_predicates

    column_name = list(filters.keys())[0]

    try:
        column = _COLUMN_MAPPING[column_name]
    except KeyError:
        raise Exception("Unknown filter field: {}".format(column_name))

    filter = filters[column_name]
    if len(filter) == 0:
        raise Exception("Empty filter: {}".format(filters))

    operator = list(filter.keys())[0]
    value = filter[operator]

    # Will obviously need to add more, only supporting eq for now
    if operator == "eq":
        sql_predicates.append(column == value)

    return sql_predicates


@glow_api.route("/api/v1/runs", methods=["GET"])
def list_runs_endpoint() -> flask.Response:
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
    limit, cursor, group_by, sql_predicates = _get_request_parameters(
        flask.request.args
    )

    decoded_cursor: typing.Optional[str] = None
    if cursor is not None:
        try:
            decoded_cursor = base64.urlsafe_b64decode(bytes(cursor, "utf-8")).decode(
                "utf-8"
            )
        except Exception:
            raise Exception("invalid cursor")

    with db().get_session() as session:
        query = session.query(Run)

        if group_by is not None:
            query = query.group_by(group_by)

        if len(sql_predicates) > 0:
            query = query.filter(*sql_predicates)

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

        runs: typing.List[Run] = query.limit(limit).all()
        after_cursor_count: int = query.count()

    current_url_params: typing.Dict[str, str] = dict(limit=str(limit))
    if cursor is not None:
        current_url_params["cursor"] = cursor

    scheme, netloc, path, _, fragment = urlsplit(flask.request.url)
    current_page_url = urlunsplit(
        (scheme, netloc, path, urlencode(current_url_params), fragment)
    )

    next_page_url: typing.Optional[str] = None
    next_cursor: typing.Optional[str] = None

    if runs and after_cursor_count > limit:
        next_url_params: typing.Dict[str, str] = dict(limit=str(limit))
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
