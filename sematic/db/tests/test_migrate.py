# Standard library
from unittest.mock import patch
import sqlite3

# Third-party
import pytest

# Sematic
from sematic.db.migrate import migrate


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
