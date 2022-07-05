# Standard library
from http import HTTPStatus
from typing import Dict, Literal, Tuple, Optional, List, Union, cast
import json

# Third-party
import flask
import sqlalchemy
from sqlalchemy.sql.elements import ColumnElement, BooleanClauseList

# Default page size
DEFAULT_LIMIT = 20


ColumnMapping = Dict[str, sqlalchemy.Column]

Scalar = Union[str, int, float, bool, None]
ColumnPredicate = Dict[str, Dict[str, Union[Scalar, List[Scalar]]]]
BooleanPredicate = Dict[Literal["AND", "OR"], List[ColumnPredicate]]

Filters = Union[
    ColumnPredicate,
    BooleanPredicate,
]


def get_request_parameters(
    args: Dict[str, str], model: type
) -> Tuple[
    int, Optional[str], Optional[sqlalchemy.Column], Optional[BooleanClauseList]
]:
    """
    Extract, validate, and format query parameters.

    Parameters
    ----------
    args : Dict[str, str]
        request argument as returned by `flask.request.args`.

    Returns
    Tuple[int, Optional[str], Optional[str], List[ColumnElement]]
        limit, custor, group_by, filters
    """
    limit: int = int(args.get("limit", DEFAULT_LIMIT))
    if not (limit == -1 or limit > 0):
        raise Exception("limit must be greater than 0 or -1")

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
            raise ValueError("Unsupported group_by value {}".format(repr(group_by)))

        group_by_column = column_mapping[group_by]

    filters_json: str = args.get("filters", "{}")
    filters: Dict = {}
    try:
        filters = json.loads(filters_json)
    except Exception as e:
        raise Exception("Malformed filters: {}, error: {}".format(filters_json, e))

    sql_predicates = (
        _get_sql_predicates(filters, column_mapping) if len(filters) > 0 else None
    )

    return limit, cursor, group_by_column, sql_predicates


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
    Basic support for a AND filter predicate.

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
    ```
    """
    operand = list(filters.keys())[0]

    if operand in {"AND", "OR"}:
        filters = cast(BooleanPredicate, filters)
        operand = cast(Literal["AND", "OR"], operand)
        operator = dict(AND=sqlalchemy.and_, OR=sqlalchemy.or_)[operand]
        return operator(
            *[
                _extract_single_predicate(filter, column_mapping)
                for filter in filters[operand]
            ]
        )
    else:
        filters = cast(ColumnPredicate, filters)
        return sqlalchemy.and_(_extract_single_predicate(filters, column_mapping))


def _extract_single_predicate(
    filter: ColumnPredicate, column_mapping: ColumnMapping
) -> ColumnElement:
    column_name = list(filter.keys())[0]

    try:
        column = column_mapping[column_name]
    except KeyError:
        raise Exception("Unknown filter field: {}".format(column_name))

    condition = filter[column_name]
    if len(condition) == 0:
        raise Exception("Empty filter: {}".format(filter))

    operator = list(condition.keys())[0]
    value = condition[operator]

    # Will obviously need to add more, only supporting eq for now
    if operator == "eq":
        return column == value

    if operator == "in":
        return column.in_(value)

    raise NotImplementedError("Unsupported filter: {}".format(filter))
