"""
When users hit

$ sematic start

The SQLite DB should be migrated to the latest version
automatically.

On the dev side, we use dbmate to create and run migrations. One option would
have been to package it with the wheel and run it in a subprocess, but Macs are
not friendly with arbitrary binaries being downloaded and launched (need to
activate permissions). The option chosen here is to replicate a simple UP script
in Python that can be called by the CLI. The script only supports SQLite for
now.
"""
# Standard library
import os
import sqlite3
from typing import List

# Sematic
from sematic.config import get_config, SQLITE_FILE


def _get_conn() -> sqlite3.Connection:
    """
    We break this out to enable mocking in tests.
    """
    sqlite_file_path = os.path.join(get_config().config_dir, SQLITE_FILE)

    return sqlite3.connect(sqlite_file_path)


def _get_migration_files() -> List[str]:
    migrations_dir = get_config().migrations_dir

    return sorted(os.listdir(migrations_dir))


def migrate():
    """
    Will migrate the SQLite DB sitting at `get_config().config_dir, SQLITE_FILE`
    to the latest version.
    """

    conn = _get_conn()

    with conn:
        conn.execute(
            (
                "CREATE TABLE IF NOT EXISTS "
                '"schema_migrations" (version varchar(255) primary key);'
            )
        )

    schema_migrations = conn.execute("SELECT version FROM schema_migrations;")

    versions = [row[0] for row in schema_migrations]

    migration_files = _get_migration_files()

    for migration_file in migration_files:
        version = migration_file.split("_")[0]
        if version in versions:
            continue

        with open(
            os.path.join(get_config().migrations_dir, migration_file), "r"
        ) as file:
            sql = file.read()

        up_sql = sql.split("-- migrate:down")[0].split("-- migrate:up")[1].strip()

        statements = up_sql.split(";")

        with conn:
            for statement in statements:
                if len(statement) == 0:
                    continue

                conn.execute("{};".format(statement))

            conn.execute(
                "INSERT INTO schema_migrations(version) values (?)", (version,)
            )


if __name__ == "__main__":
    migrate()
