# Standard Library
import json

# Sematic
from sematic.db.db import db
from sematic.db.models.run import Run
from sematic.utils.exceptions import ExceptionMetadata


def up():
    with db().get_engine().connect() as conn:
        run_id_exception_pairs = conn.execute(
            "SELECT id, exception FROM runs WHERE exception IS NOT NULL;"
        )

        exception_map = {pair[0]: pair[1] for pair in run_id_exception_pairs}

    with db().get_session() as session:
        runs_with_exceptions = (
            session.query(Run).filter(Run.id.in_(exception_map.keys())).all()
        )

    runs_by_id = {run.id: run for run in runs_with_exceptions}

    for run_id, exception in exception_map.items():
        runs_by_id[run_id].exception = ExceptionMetadata(
            repr=exception, name=Exception.__name__, module=Exception.__module__
        )

    with db().get_session() as session:
        session.add_all(runs_with_exceptions)
        session.commit()


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
