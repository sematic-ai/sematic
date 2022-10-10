"""
When users hit

$ sematic start

The SQLite DB should be migrated to the latest version
automatically.
"""
# Standard Library
import enum
import functools
import importlib
import logging
import os
import subprocess
from typing import List, Optional
from urllib.parse import urlparse

# Third-party
import click
from sqlalchemy import text
from sqlalchemy.engine import Connection

# Sematic
from sematic.config import get_config, switch_env
from sematic.db.db import db


def _get_migration_files() -> List[str]:
    migrations_dir = get_config().migrations_dir

    return sorted(
        file_name
        for file_name in os.listdir(migrations_dir)
        if _is_migration_file(file_name)
    )


def _is_migration_file(file_name: str) -> bool:
    parts = file_name.split("_")
    return (
        len(parts) > 0
        and len(parts[0]) == 14
        and parts[0].isdigit()
        and file_name.split(".")[-1] in ("sql", "py")
    )


def _get_current_versions() -> List[str]:
    with db().get_engine().connect() as conn:
        conn.execute(
            (
                "CREATE TABLE IF NOT EXISTS "
                '"schema_migrations" (version varchar(255) primary key);'
            )
        )

        schema_migrations = conn.execute(
            "SELECT version FROM schema_migrations ORDER BY version ASC;"
        )

        versions = [row[0] for row in schema_migrations]

    return versions


class MigrationDirection(enum.Enum):
    UP = "UP"
    DOWN = "DOWN"


def _run_migration(migration_file: str, version: str, direction: MigrationDirection):
    action = "Applying" if direction == MigrationDirection.UP else "Reverting"
    logging.info(f"{action} {migration_file}")

    extension = migration_file.split(".")[-1]

    if extension == "sql":
        _run_sql_migration(migration_file, version, direction)

    if extension == "py":
        _run_py_migration(migration_file, version, direction)


def _get_migration_sql(migration_file: str) -> str:
    """
    Read migration SQL from file.
    """
    with open(os.path.join(get_config().migrations_dir, migration_file), "r") as file:
        return file.read()


_DOWN_MARKER = "-- migrate:down"
_UP_MARKER = "-- migrate:up"


class InvalidMigrationError(ValueError):
    pass


def _run_sql_migration(
    migration_file: str, version: str, direction: MigrationDirection
):
    sql = _get_migration_sql(migration_file)

    if not all(marker in sql for marker in (_DOWN_MARKER, _UP_MARKER)):
        raise InvalidMigrationError(
            f"{migration_file} does not contain the required markers: "
            f"{_UP_MARKER} and {_DOWN_MARKER}"
        )

    up_sql, down_sql = sql.split(_DOWN_MARKER)
    up_sql = up_sql.split(_UP_MARKER)[1].strip()
    down_sql = down_sql.strip()

    statements = (up_sql if direction == MigrationDirection.UP else down_sql).split(";")

    with db().get_engine().begin() as conn:
        for statement in statements:
            if len(statement) == 0:
                continue

            conn.execute("{};".format(statement))

        _update_version(conn, version, direction)


def _run_py_migration(migration_file: str, version: str, direction: MigrationDirection):
    module = importlib.import_module(
        f"sematic.db.migrations.{migration_file.split('.')[0]}"
    )

    up, down = getattr(module, "up"), getattr(module, "down")

    try:
        up() if direction == MigrationDirection.UP else down()

        with db().get_engine().begin() as conn:
            _update_version(conn, version, direction)

    except Exception as e:
        down() if direction == MigrationDirection.UP else up()
        raise e


def _update_version(conn: Connection, version: str, direction: MigrationDirection):
    statement = (
        "INSERT INTO schema_migrations(version) values (:version)"
        if direction == MigrationDirection.UP
        else "DELETE FROM schema_migrations WHERE version = :version"
    )

    conn.execute(text(statement), version=version)


def common_options(f):
    options = [
        click.option(
            "--env",
            "env",
            type=click.STRING,
            help="Environment in which to run migrations.",
            default="local",
        ),
        click.option(
            "--verbose", "verbose", is_flag=True, default=False, help="INFO log level"
        ),
    ]
    return functools.reduce(lambda x, opt: opt(x), options, f)


@click.group("migrate")
@common_options
def main(env: str, verbose: bool):
    _apply_common_options(env, verbose)


def _apply_common_options(env, verbose):
    switch_env(env)

    if verbose:
        logging.basicConfig(level=logging.INFO)


@main.command("up", short_help="Apply outstanding migrations")
@common_options
@click.option(
    "--schema-file",
    "file",
    type=click.STRING,
    default="schema.sql",
    help="File into which to dump the new schema.",
)
def _migrate_up(env: str, verbose: bool, file: str):
    """
    Migrate the DB to the latest version.
    """
    _apply_common_options(env, verbose)
    # Separate function to be able to invoke it outside of click
    migrate_up()
    dump_schema(file)


def migrate_up():
    """
    Migrate the DB to the latest version.
    """
    logging.info("Running migrations on {}".format(get_config().db_url))

    versions = _get_current_versions()

    migration_files = _get_migration_files()

    last_successful: Optional[str] = None

    for migration_file in migration_files:
        version = migration_file.split("_")[0]

        if version in versions:
            logging.info("Already applied {}".format(migration_file))
            continue

        try:
            _run_migration(migration_file, version, MigrationDirection.UP)
        except Exception as e:
            logging.error(
                f"{migration_file} failed with error:\n"
                f"{e}\n"
                f"Last successful migration is: {last_successful}"
            )
            return

        last_successful = migration_file


@main.command("down", short_help="Revert last migration")
@common_options
@click.option(
    "--schema-file",
    "file",
    type=click.STRING,
    default="schema.sql",
    help="File into which to dump the new schema.",
)
def _migrate_down(env: str, verbose: bool, file: str):
    """
    Revert the last migration.
    """
    _apply_common_options(env, verbose)
    # Separate function to be able to invoke it outside of click
    migrate_down()
    dump_schema(file)


def migrate_down():
    """
    Revert the last migration.
    """
    current_versions = _get_current_versions()

    if len(current_versions) == 0:
        logging.warning("No migrations to rollback")
        return

    latest_version = current_versions[-1]

    migration_file = next(
        f for f in _get_migration_files() if f.startswith(latest_version)
    )

    _run_migration(migration_file, latest_version, MigrationDirection.DOWN)


@main.command("dump", short_help="Dump schema")
@common_options
@click.option(
    "--schema-file",
    "file",
    type=click.STRING,
    default="schema.sql",
    help="File to dump the schema to.",
)
def _dump_schema(env: str, verbose: bool, file: str):
    _apply_common_options(env, verbose)
    dump_schema(file)


def dump_schema(file: str):
    parsed_db_url = urlparse(get_config().db_url)

    if parsed_db_url.scheme != "sqlite":
        logging.warning("Not dumping schema, only SQLite supported at this time")
        return

    db_file_path = parsed_db_url.path

    schema = (
        subprocess.Popen(  # type: ignore
            f"sqlite3 {db_file_path} .schema",
            shell=True,
            stdout=subprocess.PIPE,
        )
        .stdout.read()
        .decode("utf-8")
    )

    current_versions = _get_current_versions()

    schema += (
        ("-- schema migrations\n" 'INSERT INTO "schema_migrations" (version) VALUES\n')
        + ",\n".join(f"  ('{version}')" for version in current_versions)
        + ";\n"
    )

    logging.info("Writing schema to %s", file)
    with open(file, "w") as f:
        f.write(schema)


@main.command("status", short_help="Current migration status")
@common_options
def status(env: str, verbose: bool):
    _apply_common_options(env, verbose)

    current_versions = _get_current_versions()
    migration_files = _get_migration_files()

    applied_count, outstanding_count = 0, 0

    for migration_file in migration_files:
        version = migration_file.split("_")[0]

        if version in current_versions:
            mark = "x"
            applied_count += 1
        else:
            mark = " "
            outstanding_count += 1

        print(f"[{mark}]\t{migration_file}")

    print(f"\nApplied:\t{applied_count:3}")
    print(f"Outstanding:\t{outstanding_count:3}")


if __name__ == "__main__":
    main()
