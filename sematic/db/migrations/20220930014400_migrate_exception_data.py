# Standard Library
import json

# Third-party
from sqlalchemy import text

# Sematic
from sematic.db.db import db


def up():
    with db().get_engine().begin() as conn:
        run_id_exception_pairs = conn.execute(
            text("SELECT id, exception FROM runs WHERE exception IS NOT NULL;")
        )

        for run_id, exception in run_id_exception_pairs:
            exception_metadata = dict(
                repr=exception, name=Exception.__name__, module=Exception.__module__
            )
            exception_json = json.dumps(exception_metadata)

            conn.execute(
                text("UPDATE runs SET exception_json = :e_json WHERE id = :run_id"),
                dict(
                    e_json=exception_json,
                    run_id=run_id,
                ),
            )


def down():
    with db().get_engine().begin() as conn:
        # TODO #303: standardize NULL vs 'null'
        run_id_exception_json_pairs = conn.execute(
            text(
                "SELECT id, exception_json FROM runs "
                "WHERE exception_json IS NOT NULL AND exception_json IS NOT 'null';"
            )
        )

        for run_id, exception_json in run_id_exception_json_pairs:
            exception = json.loads(exception_json)["repr"]
            conn.execute(
                text("UPDATE runs SET exception = :e WHERE id = :run_id"),
                dict(e=exception, run_id=run_id),
            )
