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
            "id, name "
            "FROM runs "
            "WHERE function_path IS NULL;"
        )

        print('runs function_path', list(results))

        results = conn.execute(
            "SELECT "
            "id, created_at"
            "FROM artifacts "
            "WHERE type_serialization IS NULL;"
        )

        print('artifacts type_serialization', list(results))

        results = conn.execute(
            "SELECT "
            "run_id, name "
            "FROM jobs "
            "WHERE created_at IS NULL;"
        )

        print('jobs created_at', list(results))

        results = conn.execute(
            "SELECT "
            "run_id, name, created_at "
            "FROM jobs "
            "WHERE updated_at IS NULL;"
        )

        print('jobs updated_at', list(results))

        results = conn.execute(
            "SELECT "
            "id "
            "FROM notes "
            "WHERE created_at IS NULL;"
        )

        print('notes created_at', list(results))

        results = conn.execute(
            "SELECT "
            "id, created_at "
            "FROM notes "
            "WHERE updated_at IS NULL;"
        )

        print('notes updated_at', list(results))

        results = conn.execute(
            "SELECT "
            "id, created_at "
            "FROM runs "
            "WHERE root_id IS NULL;"
        )

        print('runs root_id', list(results))

        results = conn.execute(
            "SELECT "
            "id, created_at "
            "FROM runs "
            "WHERE tags IS NULL;"
        )

        print('runs tags', list(results))

        results = conn.execute(
            "SELECT "
            "id, created_at "
            "FROM runs "
            "WHERE source_code IS NULL;"
        )

        print('runs source_code', list(results))

        results = conn.execute(
            "SELECT "
            "edges.source_run_id, edges.destination_run_id, edges.destination_name, edges.created_at "
            "FROM edges LEFT OUTER JOIN runs ON edges.destination_run_id = runs.id "
            "WHERE runs.id IS NULL;"
        )

        print('edges destination_run_id', list(results))

        results = conn.execute(
            "SELECT "
            "edges.source_run_id, edges.destination_run_id, edges.destination_name, edges.created_at "
            "FROM edges LEFT OUTER JOIN runs ON edges.source_run_id = runs.id "
            "WHERE runs.id IS NULL;"
        )

        print('edges source_run_id', list(results))

        results = conn.execute(
            "SELECT "
            "metric_values.metric_id, metric_values.created_at "
            "FROM metric_values LEFT OUTER JOIN metric_labels ON metric_values.metric_id = metric_labels.metric_id "
            "WHERE metric_labels.metric_id IS NULL;"
        )

        print('metric_values metric_id', list(results))

        results = conn.execute(
            "SELECT "
            "runs_left.id, runs_left.name "
            "FROM runs runs_left LEFT OUTER JOIN runs runs_right ON runs_left.id = runs_right.id "
            "WHERE runs_right.id IS NULL;"
        )

        print('runs root_id fk', list(results))

if __name__ == '__main__':
    up()

# 45 SELECT edges.source_run_id, edges.destination_run_id, edges.destination_name, edges.created_at FROM edges LEFT OUTER JOIN runs ON edges.destination_run_id = runs.id WHERE runs.id IS NULL;
# 263 SELECT edges.source_run_id, edges.destination_run_id, edges.destination_name, edges.created_at FROM edges LEFT OUTER JOIN runs ON edges.source_run_id = runs.id WHERE runs.id IS NULL;
# 0 SELECT metric_values.metric_id, metric_values.created_at FROM metric_values LEFT OUTER JOIN metric_labels ON metric_values.metric_id = metric_labels.metric_id WHERE metric_labels.metric_id IS NULL;
# 0 SELECT runs_left.id, runs_left.name FROM runs runs_left LEFT OUTER JOIN runs runs_right ON runs_left.id = runs_right.id WHERE runs_right.id IS NULL;
