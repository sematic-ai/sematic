# Standard Library
import uuid

# Third-party
from sqlalchemy.sql import text

# Sematic
from sematic.db.db import db


def up():
    with db().get_engine().begin() as conn:
        results = conn.execute(
            "SELECT "
            "* "
            "FROM runs "
            "WHERE function_path IS NULL;"
        )

        print('runs function_path', list(results))

        results = conn.execute(
            "SELECT "
            "* "
            "FROM artifacts "
            "WHERE type_serialization IS NULL;"
        )

        print('artifacts type_serialization', list(results))

        results = conn.execute(
            "SELECT "
            "* "
            "FROM jobs "
            "WHERE created_at IS NULL;"
        )

        print('jobs created_at', list(results))

        results = conn.execute(
            "SELECT "
            "* "
            "FROM jobs "
            "WHERE updated_at IS NULL;"
        )

        print('jobs updated_at', list(results))

        results = conn.execute(
            "SELECT "
            "* "
            "FROM notes "
            "WHERE created_at IS NULL;"
        )

        print('notes created_at', list(results))

        results = conn.execute(
            "SELECT "
            "* "
            "FROM notes "
            "WHERE updated_at IS NULL;"
        )

        print('notes updated_at', list(results))

        results = conn.execute(
            "SELECT "
            "* "
            "FROM runs "
            "WHERE root_id IS NULL;"
        )

        print('runs root_id', list(results))

        results = conn.execute(
            "SELECT "
            "* "
            "FROM runs "
            "WHERE tags IS NULL;"
        )

        print('runs tags', list(results))

        results = conn.execute(
            "SELECT "
            "* "
            "FROM runs "
            "WHERE source_code IS NULL;"
        )

        print('runs source_code', list(results))

        results = conn.execute(
            "SELECT "
            "* "
            "FROM edges "
            "WHERE destination_run_id IS NOT NULL "
            "AND destination_run_id NOT IN ( "
            "   SELECT id "
            "   FROM runs "
            ");"
        )

        print('edges destination_run_id', list(results))

        results = conn.execute(
            "SELECT "
            "* "
            "FROM edges "
            "WHERE source_run_id IS NOT NULL "
            "AND source_run_id NOT IN ( "
            "   SELECT id "
            "   FROM runs "
            ");"
        )

        print('edges source_run_id', list(results))

        results = conn.execute(
            "SELECT "
            "* "
            "FROM metric_values "
            "WHERE metric_id IS NOT NULL "
            "AND metric_id NOT IN ( "
            "   SELECT metric_id "
            "   FROM metric_labels "
            ");"
        )

        print('metric_values metric_id', list(results))

        results = conn.execute(
            "SELECT "
            "* "
            "FROM runs "
            "WHERE root_id IS NOT NULL "
            "AND root_id NOT IN ( "
            "   SELECT id "
            "   FROM runs "
            ");"
        )

        print('runs root_id fk', list(results))

if __name__ == '__main__':
    up()
