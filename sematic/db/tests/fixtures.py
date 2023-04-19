# Standard Library
import time
import uuid
from typing import Any

# Third-party
import psycopg2
import pytest
import testing.postgresql  # type: ignore

# Sematic
import sematic.db.db as db
from sematic.abstract_future import FutureState
from sematic.db.models.external_resource import ExternalResource
from sematic.db.models.factories import make_artifact
from sematic.db.models.factories import make_job as factory_make_job
from sematic.db.models.factories import make_user
from sematic.db.models.git_info import GitInfo
from sematic.db.models.job import Job
from sematic.db.models.resolution import Resolution, ResolutionKind, ResolutionStatus
from sematic.db.models.run import Run
from sematic.db.queries import (
    _save_artifact,
    save_external_resource_record,
    save_resolution,
    save_run,
    save_user,
)
from sematic.plugins.abstract_external_resource import AbstractExternalResource
from sematic.resolvers.resource_requirements import (
    KubernetesResourceRequirements,
    ResourceRequirements,
)
from sematic.scheduling.job_details import (
    JobDetails,
    JobKind,
    JobStatus,
    KubernetesJobState,
)
from sematic.tests.fixtures import test_storage  # noqa: F401


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


def make_job(**kwargs) -> Job:
    final_kwargs = dict(
        name="foo",
        namespace="bar",
        run_id="abc123",
        status=JobStatus(
            state=KubernetesJobState.Requested,  # type: ignore
            message="Just created",
            last_updated_epoch_seconds=time.time(),
        ),
        details=JobDetails(try_number=0),
        kind=JobKind.run,
    )
    final_kwargs.update(kwargs)
    return factory_make_job(**final_kwargs)  # type: ignore


def make_run(**kwargs) -> Run:
    id = uuid.uuid4().hex
    run = Run(
        id=id,
        original_run_id=None,
        future_state=FutureState.CREATED,
        name="test_run",
        calculator_path="path.to.test_run",
        root_id=id,
        container_image_uri="foobar",
        description="Foo Bar",
        tags=["foo", "bar"],
        source_code="def foo(): pass",
        cache_key=None,
        user_id=None,
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
        container_image_uris={"default": "some.uri"},
        container_image_uri="some.uri",
        settings_env_vars={"MY_SETTING": "MY_VALUE"},
        user_id=None,
    )

    # Set this outside the constructor because the constructor expects
    # a json encodable, but this property will auto-update the json
    # encodable field.
    resolution.git_info = GitInfo(
        remote="remote", branch="branch", commit="commit", dirty=False
    )

    for name, value in kwargs.items():
        setattr(resolution, name, value)

    return resolution


@pytest.fixture
def persisted_external_resource(test_db) -> AbstractExternalResource:
    return save_external_resource_record(
        ExternalResource.from_resource(AbstractExternalResource())
    )


@pytest.fixture
def run() -> Run:
    return make_run()


@pytest.fixture
def allow_any_run_state_transition():
    original = FutureState.is_allowed_transition
    try:
        FutureState.is_allowed_transition = lambda *args, **kwargs: True
        yield
    finally:
        FutureState.is_allowed_transition = original


@pytest.fixture
def persisted_run(run, test_db, allow_any_run_state_transition) -> Run:  # noqa: F811
    return save_run(run)


@pytest.fixture
def persisted_run_w_user(
    persisted_user, test_db, allow_any_run_state_transition
) -> Run:  # noqa: F811
    # run's user_id is a foreign key to the users table,
    # so we need a persisted user to get a persisted run with a user.
    return save_run(make_run(user_id=persisted_user.id))


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
def persisted_resolution_w_user(
    persisted_run_w_user, persisted_user, test_db
) -> Resolution:
    # resolution's key is a foreign key to the runs table,
    # so we need a persisted run to get a persisted resolution.
    # resolution's user_id is a foreign key to the users table,
    # so we need a persisted user to get a persisted resolution with a user.
    resolution = make_resolution(
        root_id=persisted_run_w_user.id, user_id=persisted_user.id
    )
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
def other_persisted_user(test_db):  # noqa: F811
    user = make_user(
        email="ringo@example.com",
        first_name="Ringo",
        last_name="Starr",
        avatar_url="https://avatar",
    )
    save_user(user)
    return user


@pytest.fixture
def persisted_artifact(test_db, test_storage):  # noqa: F811
    """
    Persisted artifact fixture.
    """
    artifact, upload_payloads = make_artifact(42, int)

    with db.db().get_session() as session:
        artifact = _save_artifact(artifact=artifact, session=session)
        session.commit()
        session.refresh(artifact)

    for payload in upload_payloads:
        test_storage.set(f"{payload.namespace.value}/{payload.key}", payload.payload)

    return artifact
