# Standard Library
import json

# Sematic
from sematic.db.db import db


def up():
    with db().get_engine().begin() as conn:
        run_id_exception_pairs = conn.execute(
            "SELECT id, exception FROM runs WHERE exception IS NOT NULL;"
        )

        for run_id, exception in run_id_exception_pairs:
            exception_metadata = dict(
                repr=exception, name=Exception.__name__, module=Exception.__module__
            )
            exception_json = json.dumps(exception_metadata)

            conn.execute(
                "UPDATE runs SET exception_json = ? WHERE id = ?",
                exception_json,
                run_id,
            )


def down():
    with db().get_engine().connect() as conn:
        run_id_exception_json_pairs = conn.execute(
            "SELECT id, exception_json FROM runs WHERE exception_json IS NOT NULL;"
        )

        for run_id, exception_json in run_id_exception_json_pairs:
            exception = json.loads(exception_json)["repr"]
            conn.execute(
                "UPDATE runs SET exception = ? WHERE id = ?", exception, run_id
            )
