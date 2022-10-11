# Standard Library
import uuid
from typing import Any

# Third-party
import psycopg2
import pytest
import testing.postgresql  # type: ignore

# Sematic
import sematic.db.db as db
from sematic.abstract_future import FutureState
from sematic.db.models.factories import make_artifact, make_user
from sematic.db.models.resolution import Resolution, ResolutionKind, ResolutionStatus
from sematic.db.models.run import Run
from sematic.db.queries import save_resolution, save_run, save_user
from sematic.resolvers.resource_requirements import (
    KubernetesResourceRequirements,
    ResourceRequirements,
)
from sematic.tests.fixtures import test_storage  # noqa: F401
from sematic.utils.git import GitInfo


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
    run.resource_requirements = ResourceRequirements(
        kubernetes=KubernetesResourceRequirements(
            requests={"cpu": "42"},
        )
    )

    for name, value in kwargs.items():
        setattr(run, name, value)

    return run


def make_resolution(**kwargs) -> Resolution:
    root_id = uuid.uuid4().hex
    resolution = Resolution(
        root_id=root_id,
        status=ResolutionStatus.SCHEDULED,
        kind=ResolutionKind.KUBERNETES,
        docker_image_uri="some.uri",
        git_info=GitInfo(remote="remote", branch="branch", commit="commit", dirty=False),
        settings_env_vars={"MY_SETTING": "MY_VALUE"},
    )

    for name, value in kwargs.items():
        setattr(resolution, name, value)

    return resolution


@pytest.fixture
def run() -> Run:
    return make_run()


@pytest.fixture
def persisted_run(run, test_db) -> Run:
    return save_run(run)


@pytest.fixture
def resolution() -> Resolution:
    return make_resolution()


@pytest.fixture
def persisted_resolution(persisted_run, test_db) -> Resolution:
    # resolution's key is a foreign key to the runs table,
    # so we need a persisted run to get a persisted resolution.
    resolution = make_resolution(root_id=persisted_run.id)
    return save_resolution(resolution)


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


@pytest.fixture
def persisted_artifact(test_db, test_storage):  # noqa: F811
    """
    Persisted artifact fixture.
    """
    artifact = make_artifact(42, int, True)

    with db.db().get_session() as session:
        session.add(artifact)
        session.commit()
        session.refresh(artifact)

    return artifact
