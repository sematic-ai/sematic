# Standard Library
from unittest.mock import patch

# Third-party
import pytest
from sqlalchemy.exc import OperationalError

# Sematic
from sematic.db.db import db
from sematic.db.migrate import (
    InvalidMigrationError,
    MigrationDirection,
    _get_current_versions,
    _get_migration_files,
    _run_sql_migration,
    migrate_down,
    migrate_up,
)
from sematic.db.tests.fixtures import test_db_empty  # noqa: F401


@patch("sematic.db.migrate._get_migration_sql", return_value="")
def test_invalid_migration(_):
    with pytest.raises(InvalidMigrationError):
        _run_sql_migration("abc", "abc", MigrationDirection.UP)


INVALID_SQL = """
-- migrate:up

SELECT;

-- migrate:down

"""


@patch("sematic.db.migrate._get_migration_sql", return_value=INVALID_SQL)
def test_invalid_sql(_, test_db_empty):  # noqa: F811
    current_versions = _get_current_versions()

    assert len(current_versions) == 0

    with pytest.raises(OperationalError):
        _run_sql_migration("abc", "abc", MigrationDirection.UP)

    current_versions = _get_current_versions()

    assert len(current_versions) == 0


@patch("sematic.db.migrate._run_py_migration")
def test_migrate(_, test_db_empty):  # noqa: F811

    with pytest.raises(OperationalError):
        with db().get_engine().connect() as conn:
            conn.execute("SELECT version FROM schema_migrations;")

    migrate_up()

    current_versions = _get_current_versions()

    assert len(current_versions) > 0

    # Test tables were created
    with db().get_engine().connect() as conn:
        run_count = conn.execute("SELECT COUNT(*) from runs;")

    assert list(run_count)[0][0] == 0

    migrate_down()

    new_current_versions = _get_current_versions()

    assert len(new_current_versions) == len(current_versions) - 1
    assert set(current_versions) - set(new_current_versions) == {current_versions[-1]}


def test_get_migration_files():
    """
    Tests that the actual migration files are returned.
    """
    migration_files = _get_migration_files()

    assert len(migration_files) > 0
    assert all(
        migration_file.split(".")[-1] in ("sql", "py")
        for migration_file in migration_files
    )


# Make sure return_value is unordered
@patch(
    "sematic.db.migrate.os.listdir",
    return_value=["20220521155336", "20220424062956", "20220522082435"],
)
@patch("sematic.db.migrate._is_migration_file", return_value=True)
def test_get_migration_files_sorted(_, __):
    """
    Tests that migration files are sorted.
    """
    migration_files = _get_migration_files()
    assert migration_files == ["20220424062956", "20220521155336", "20220522082435"]
