# Standard library
import uuid

# Third-party
import pytest
import testing.postgresql  # type: ignore
import psycopg2

# Glow
import glow.db.db as db
from glow.db.models.run import Run
from glow.abstract_future import FutureState
from glow.db.queries import save_run


def handler(postgresql):
    with open("glow/db/schema.sql", "r") as f:
        schema = f.read()

    conn = psycopg2.connect(**postgresql.dsn())

    cursor = conn.cursor()
    cursor.execute(schema)
    # Needed because the schema creates tables in the public schema.
    cursor.execute("SET search_path=public;")
    cursor.close()
    conn.commit()
    conn.close()


# Use `handler()` on initialize database
Postgresql = testing.postgresql.PostgresqlFactory(
    cache_initialized_db=True, on_initialized=handler
)


@pytest.fixture(scope="module")
def pg_mock():
    try:
        yield
    finally:
        Postgresql.clear_cache()


@pytest.fixture(scope="function")
def test_db(pg_mock):
    postgresql = Postgresql()
    previous_instance = db._db_instance
    db._db_instance = db.DB(postgresql.url())
    try:
        yield postgresql
    finally:
        postgresql.stop()
        db._db_instance = previous_instance


@pytest.fixture(scope="function")
def test_sqlite_db():
    original_db = db._db_instance
    temp_db = db.LocalDB("sqlite://")

    with open("glow/db/schema.sql", "r") as file:
        schema = file.read()

    connection = temp_db.get_engine().raw_connection()
    cursor = connection.cursor()
    cursor.executescript(schema)

    db._db_instance = temp_db

    try:
        yield temp_db
    finally:
        db._db_instance = original_db


def make_run(**kwargs) -> Run:
    id = uuid.uuid4().hex
    run = Run(
        id=id,
        future_state=FutureState.CREATED,
        name="test_run",
        calculator_path="path.to.test_run",
        root_id=id,
    )

    for name, value in kwargs.items():
        setattr(run, name, value)

    return run


@pytest.fixture
def run() -> Run:
    return make_run()


@pytest.fixture
def persisted_run(run, test_db) -> Run:
    return save_run(run)
