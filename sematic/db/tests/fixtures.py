# Standard library
import uuid
from typing import Any

# Third-party
import pytest
import testing.postgresql  # type: ignore
import psycopg2

# Sematic
import sematic.db.db as db
from sematic.db.models.run import Run
from sematic.abstract_future import FutureState
from sematic.db.queries import save_run, save_user
from sematic.db.models.factories import make_user


def handler(postgresql):
    with open("sematic/db/schema.sql.pg", "r") as f:
        schema = f.read()

    conn = psycopg2.connect(**postgresql.dsn())

    cursor = conn.cursor()
    cursor.execute(schema)
    # Needed because the schema creates tables in the public schema.
    cursor.execute("SET search_path=public;")
    cursor.close()
    conn.commit()
    conn.close()


_Postgresql: Any = None


def _get_postgre():
    global _Postgresql
    if _Postgresql is None:
        # Use `handler()` on initialize database
        _Postgresql = testing.postgresql.PostgresqlFactory(
            cache_initialized_db=True, on_initialized=handler
        )
    return _Postgresql


@pytest.fixture(scope="module")
def pg_mock():
    try:
        yield
    finally:
        _get_postgre().clear_cache()


@pytest.fixture(scope="function")
def test_db_pg(pg_mock):
    postgresql = _get_postgre()()
    previous_instance = db._db_instance
    db._db_instance = db.DB(postgresql.url())
    try:
        yield postgresql
    finally:
        postgresql.stop()
        db._db_instance = previous_instance


@pytest.fixture(scope="function")
def test_db_empty():
    original_db = db._db_instance
    temp_db = db.DB("sqlite://")
    db._db_instance = temp_db
    try:
        yield temp_db
    finally:
        db._db_instance = original_db


@pytest.fixture(scope="function")
def test_db():
    original_db = db._db_instance
    temp_db = db.DB("sqlite://")

    with open("sematic/db/schema.sql.sqlite", "r") as file:
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


@pytest.fixture
def persisted_user(test_db):  # noqa: F811
    user = make_user(
        email="george@example.com",
        first_name="George",
        last_name="Harrison",
        avatar_url="https://avatar",
    )
    save_user(user)
    return user
