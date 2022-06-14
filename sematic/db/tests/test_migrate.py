# Standard library
from unittest.mock import patch
import sqlite3

# Third-party
import pytest

# Sematic
from sematic.db.migrate import migrate, _get_migration_files


_MEMORY_CONN = sqlite3.connect(":memory:")


@patch("sematic.db.migrate._get_conn", return_value=_MEMORY_CONN)
def test_migrate(_):

    # Test no tables exist
    with pytest.raises(sqlite3.OperationalError):
        with _MEMORY_CONN:
            _MEMORY_CONN.execute("SELECT version FROM schema_migrations;")

    migrate()

    # Test tables were created
    with _MEMORY_CONN:
        _MEMORY_CONN.execute("SELECT version FROM schema_migrations;")
        run_count = _MEMORY_CONN.execute("SELECT COUNT(*) from runs;")

    assert list(run_count)[0][0] == 0


def test_get_migration_files():
    """
    Tests that the actual migration files are returned.
    """
    migration_files = _get_migration_files()

    assert len(migration_files) > 0
    assert all(migration_file.endswith(".sql") for migration_file in migration_files)


# Make sure return_value is unordered
@patch(
    "sematic.db.migrate.os.listdir",
    return_value=["20220521155336", "20220424062956", "20220522082435"],
)
def test_get_migration_files_sorted(_):
    """
    Tests that migration files are sorted.
    """
    migration_files = _get_migration_files()
    assert migration_files == ["20220424062956", "20220521155336", "20220522082435"]
