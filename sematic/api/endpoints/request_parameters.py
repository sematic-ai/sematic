# Standard Library
import json
import logging
from dataclasses import dataclass
from http import HTTPStatus
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Literal,
    Optional,
    Tuple,
    Type,
    Union,
    cast,
)
from urllib.parse import urlsplit, urlunsplit

# Third-party
import flask
import sqlalchemy
from sqlalchemy.sql.elements import BooleanClauseList, ColumnElement

logger = logging.getLogger(__name__)

# Default page size
DEFAULT_LIMIT = 20

ORDER_BY_DIRECTIONS = {
    "asc": sqlalchemy.asc,
    "desc": sqlalchemy.desc,
}

ColumnMapping = Dict[str, sqlalchemy.Column]

Scalar = Union[str, int, float, bool, None]
ColumnPredicate = Dict[str, Dict[str, Union[Scalar, List[Scalar]]]]
BooleanPredicate = Dict[Literal["AND", "OR"], List[ColumnPredicate]]

Filters = Union[
    ColumnPredicate,
    BooleanPredicate,
]


@dataclass
class SearchRequestParameters:
    limit: int
    order: Callable[[Any], Any]
    cursor: Optional[str]
    group_by: Optional[sqlalchemy.Column]
    filters: Optional[BooleanClauseList]
    fields: Optional[List[str]]


def get_gc_filters(
    request_args: Dict[str, str], supported_filters: List[str]
) -> Tuple[bool, List[str]]:
    """Get filters for garbage collection (gc).

    Garbage collection filters are either present or not, so
    when returned they are returned as a list of the names of
    filters that were present.

    Parameters
    ----------
    request_args:
        The flask request args the filters were specified in.
    supported_filters:
        The supported garbage collection filters, as a list of
        the names of said filters.

    Returns
    -------
    A tuple where the first element is a bool indicating if there were
    extra filters besides the garbage collection ones, and the second
    element is a list of garbage collection filters that were identified.
    """
    filters_json: str = request_args.get("filters", "{}")
    try:
        filters: Dict = json.loads(filters_json)
    except Exception as e:
        raise ValueError(f"Malformed filters: {filters_json}, error: {e}")

    if len(filters) == 0:
        return False, []

    operand = list(filters.keys())[0]
    contained_extra_filters = False

    if operand in {"AND", "OR"}:
        filters = cast(BooleanPredicate, filters)
        operand = cast(Literal["AND", "OR"], operand)
        garbage_filters = []
        for filter_ in filters[operand]:
            filter_name = list(filter_.keys())[0]
            if filter_name not in supported_filters:
                contained_extra_filters = True
                continue
            if filter_[filter_name] != {"eq": True}:
                raise ValueError(
                    "The filter '{}' must use the predicate {}".format(
                        filter_name, {"eq: true"}
                    )
                )
            garbage_filters.append(filter_name)

        return contained_extra_filters, garbage_filters

    else:
        filter_ = cast(ColumnPredicate, filters)
        filter_name = list(filter_.keys())[0]
        if filter_name not in supported_filters:
            return True, []
        if filter_[filter_name] != {"eq": True}:
            raise ValueError(
                "The filter '{}' must use the predicate {}".format(
                    filter_name, "{'eq': True}"
                )
            )
        return False, [filter_name]


def list_garbage_ids(
    garbage_filter: str,
    request_url: str,
    queries: Dict[str, Callable[[], List[str]]],
    model: Type[Any],
    encoded_request_args: str,
    id_field: Optional[str] = None,
) -> flask.Response:
    """Return a flask response for a search on ids of garbage data.

    Parameters
    ----------
    garbage_filter:
        A string representing which garbage collection filter is being used.
    request_url:
        The URL used to perform the search request.
    queries:
        A mapping from garbage collection filter name to a callable to perform
        the query.
    model:
        The ORM model for the object being searched over.
    encoded_request_args:
        URL-encoded query parameters for the current search request.
    id_field:
        The name of the field representing the id of the object being searched over.
        When `None`, "id" will be used as the name of the id field. Defaults to None.

    Returns
    -------
    A flask response containing the search results. The fields of the response object
    are:
    current_page_url
        URL of the current page.
    next_page_url
        Always `None` (present for compatibility with other search APIs).
    limit
        The number of results returned.
    next_cursor
        Always `None` (present for compatibility with other search APIs).
    after_cursor_count
        Always 0 (present for compatibility with other search APIs).
    content:
        A list of id JSON payloads. Each element in the returned list is a dict
        whose key is the string specified by `id_field` and whose value is an id.
    """
    request_args = dict(flask.request.args)
    id_field = id_field or "id"
    if "limit" in request_args:
        return jsonify_error(
            f"Cannot use limit with filter {garbage_filter}",
            status=HTTPStatus.BAD_REQUEST,
        )
    del request_args["filters"]
    try:
        parameters = get_request_parameters(args=request_args, model=model)
    except ValueError as e:
        return jsonify_error(str(e), HTTPStatus.BAD_REQUEST)
    if parameters.cursor is not None:
        return jsonify_error(
            f"Cannot use pagination with filter {garbage_filter}",
            status=HTTPStatus.BAD_REQUEST,
        )
    if parameters.group_by is not None:
        return jsonify_error(
            f"Cannot use group by with filter {garbage_filter}",
            status=HTTPStatus.BAD_REQUEST,
        )
    if parameters.fields != [id_field]:
        return jsonify_error(
            f"Filter {garbage_filter} must have \"fields=['{id_field}']\" set.",
            status=HTTPStatus.BAD_REQUEST,
        )

    scheme, netloc, path, _, fragment = urlsplit(request_url)
    current_page_url = urlunsplit(
        (scheme, netloc, path, encoded_request_args, fragment)
    )

    ids = queries[garbage_filter]()

    payload = dict(
        current_page_url=current_page_url,
        next_page_url=None,
        limit=len(ids),
        next_cursor=None,
        after_cursor_count=0,
        content=[{id_field: id_} for id_ in ids],
    )
    return flask.jsonify(payload)


def get_request_parameters(
    args: Dict[str, str],
    model: type,
    default_order: Literal["asc", "desc"] = "desc",
) -> SearchRequestParameters:
    """
    Extract, validate, and format query parameters.

    Parameters
    ----------
    args : Dict[str, str]
        The request argument as returned by `flask.request.args`.
    model : type
        The Sqlalchemy model for which to tailor the parameters.
    default_order : Literal["asc", "desc"]
        The default order to return in case the arguments do not specify an explicit
        order. Defaults to "desc".

    Returns
    -------
    SearchRequestParameters
    """
    logger.debug("Raw request parameters: %s; model: %s", args, model)

    limit: int = int(args.get("limit", DEFAULT_LIMIT))
    if not (limit == -1 or limit > 0):
        raise ValueError("limit must be greater than 0 or -1")

    def _none_if_empty(name: str) -> Optional[str]:
        value = args.get(name)
        if value is not None and len(value) == 0:
            value = None

        return value

    cursor = _none_if_empty("cursor")

    group_by, group_by_column = _none_if_empty("group_by"), None

    column_mapping = _get_column_mapping(model)

    if group_by is not None:
        if group_by not in column_mapping:
            raise ValueError(f"Unsupported group_by value {repr(group_by)}")

        group_by_column = column_mapping[group_by]

    filters_json: str = args.get("filters", "{}")
    try:
        filters: Dict = json.loads(filters_json)
    except Exception as e:
        raise ValueError(f"Malformed filters: {filters_json}, error: {e}")

    sql_predicates = (
        _get_sql_predicates(filters, column_mapping) if len(filters) > 0 else None
    )

    order = ORDER_BY_DIRECTIONS.get(args.get("order", default_order))
    if order is None:
        raise ValueError(
            f"invalid value for 'order'; expected one of: "
            f"{list(ORDER_BY_DIRECTIONS.keys())}; got: '{args.get('order')}'"
        )

    include_fields_json: str = args.get("fields", "null")
    try:
        include_fields: Optional[List[str]] = json.loads(include_fields_json)
    except Exception as e:
        raise ValueError(f"Malformed include fields: {include_fields}") from e

    return SearchRequestParameters(
        limit, order, cursor, group_by_column, sql_predicates, include_fields
    )


def jsonify_error(error: str, status: HTTPStatus):
    return flask.Response(
        json.dumps(dict(error=error)),
        status=status.value,
        mimetype="application/json",
    )


def _get_column_mapping(model: type) -> Dict[str, sqlalchemy.Column]:
    """
    Create a mapping of column name to column for a SQLAlchemy model.
    """
    return {column.name: column for column in model.__table__.columns}  # type: ignore


def _get_sql_predicates(
    filters: Filters, column_mapping: ColumnMapping
) -> BooleanClauseList:
    """
    Basic support for AND and OR filter predicates.

    filters are of the form:
    ```
    {"column_name": {"operator": "value"}}
    OR
    {
        "AND": [
            {"column_name": {"operator": "value"}},
            {"column_name": {"operator": "value"}}
        ]
    }
    OR
    {
        "OR": [
            {"column_name": {"operator": "value"}},
            {"column_name": {"operator": "value"}}
        ]
    }
    ```
    """
    operand = list(filters.keys())[0]

    if operand in {"AND", "OR"}:
        filters = cast(BooleanPredicate, filters)
        operand = cast(Literal["AND", "OR"], operand)
        operator = dict(AND=sqlalchemy.and_, OR=sqlalchemy.or_)[operand]
        return operator(
            *[
                _extract_single_predicate(filter_, column_mapping)
                for filter_ in filters[operand]
            ]
        )
    else:
        filter_ = cast(ColumnPredicate, filters)
        return sqlalchemy.and_(_extract_single_predicate(filter_, column_mapping))


def _extract_single_predicate(
    filter_: ColumnPredicate, column_mapping: ColumnMapping
) -> ColumnElement:
    column_name = list(filter_.keys())[0]

    try:
        column = column_mapping[column_name]
    except KeyError:
        raise Exception(f"Unknown filter field: {column_name}")

    condition = filter_[column_name]
    if len(condition) == 0:
        raise Exception(f"Empty filter: {filter_}")

    operator = list(condition.keys())[0]
    value = condition[operator]

    # Will obviously need to add more, only supporting eq and in for now
    if operator == "eq":
        return column == value

    if operator == "in":
        return column.in_(value)

    raise NotImplementedError(f"Unsupported filter: {filter_}")
