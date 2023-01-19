# Standard Library
import json
import logging
from http import HTTPStatus
from typing import Callable, Dict, List, Literal, Optional, Tuple, Union, cast

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


def get_request_parameters(
    args: Dict[str, str],
    model: type,
    default_order: Literal["asc", "desc"] = "desc",
) -> Tuple[
    int,
    Callable,
    Optional[str],
    Optional[sqlalchemy.Column],
    Optional[BooleanClauseList],
]:
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
    Tuple[
        int,
        Callable,
        Optional[str],
        Optional[sqlalchemy.Column],
        List[ColumnElement]
    ] : limit, order, cursor, group_by, filters
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

    return limit, order, cursor, group_by_column, sql_predicates


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
