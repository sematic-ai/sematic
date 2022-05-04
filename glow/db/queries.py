# Glow
from glow.db.models.run import Run
from glow.db.db import db


def count_runs() -> int:
    with db().get_session() as session:
        run_count = session.query(Run).count()

    return run_count


def create_run(run: Run) -> Run:
    with db().get_session() as session:
        session.add(run)
        session.commit()
        session.refresh(run)

    return run
