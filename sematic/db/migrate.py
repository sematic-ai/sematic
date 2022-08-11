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
# Standard Library
import argparse
import logging
import os
from typing import List

from sqlalchemy import text

# Sematic
from sematic.config import get_config, switch_env
from sematic.db.db import db


def _get_migration_files() -> List[str]:
    migrations_dir = get_config().migrations_dir

    return sorted(os.listdir(migrations_dir))


def migrate():
    """
    Will migrate the DB to the latest version.
    """

    logging.info("Running migrations on {}".format(get_config().db_url))

    with db().get_engine().connect() as conn:
        conn.execute(
            (
                "CREATE TABLE IF NOT EXISTS "
                '"schema_migrations" (version varchar(255) primary key);'
            )
        )

        schema_migrations = conn.execute("SELECT version FROM schema_migrations;")

        versions = [row[0] for row in schema_migrations]

    logging.info("Already applied: {}".format(versions))

    migration_files = _get_migration_files()

    for migration_file in migration_files:
        version = migration_file.split("_")[0]
        if version in versions:
            logging.info("Already applied {}".format(migration_file))
            continue

        logging.info("Applying {}".format(migration_file))

        with open(
            os.path.join(get_config().migrations_dir, migration_file), "r"
        ) as file:
            sql = file.read()

        up_sql = sql.split("-- migrate:down")[0].split("-- migrate:up")[1].strip()

        statements = up_sql.split(";")

        with db().get_engine().begin() as conn:
            for statement in statements:
                if len(statement) == 0:
                    continue

                conn.execute("{};".format(statement))

            conn.execute(
                text("INSERT INTO schema_migrations(version) values (:version)"),
                version=version,
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Sematic migration script")
    parser.add_argument("--env", required=False, default="local", type=str)
    parser.add_argument("--verbose", required=False, default=False, action="store_true")
    args = parser.parse_args()

    switch_env(args.env)

    if args.verbose:
        logging.basicConfig(level=logging.INFO)

    migrate()
