# flake8: noqa E501
# Standard Library
import logging

# Third-party
from sqlalchemy import text

# Sematic
from sematic.db.db import db
from sematic.db.migration_utils import back_up_db_file, reinstate_db_file_from_backup


logger = logging.getLogger(__name__)


def up_sqlite():
    back_up_db_file(suffix="0.32.0")

    with db().get_engine().begin() as conn:
        execute_text(
            conn,
            """
            CREATE TABLE resolutions_new (
                    root_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    container_image_uri TEXT,
                    settings_env_vars JSONB NOT NULL,
                    git_info_json JSONB,
                    container_image_uris JSONB,
                    client_version TEXT,
                    cache_namespace TEXT,
                    user_id character(32),
                    run_command TEXT,
                    build_config TEXT,
                    organization_id character(32),

                    PRIMARY KEY (root_id),
                    FOREIGN KEY (root_id) REFERENCES runs(id),
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (organization_id) REFERENCES organizations(id)
                );
            """,
        )
        execute_text(
            conn,
            """
            INSERT INTO resolutions_new
                SELECT
                    root_id,
                    status,
                    kind,
                    container_image_uri,
                    settings_env_vars,
                    git_info_json,
                    container_image_uris,
                    client_version,
                    cache_namespace,
                    user_id,
                    run_command,
                    build_config,
                    NULL
                FROM resolutions;
            """,
        )
        execute_text(conn, "DROP TABLE resolutions;")
        execute_text(conn, "ALTER TABLE resolutions_new RENAME TO resolutions;")

        execute_text(
            conn,
            """
            CREATE TABLE runs_new (
                    id character(32) NOT NULL,
                    future_state TEXT NOT NULL,
                    name TEXT,
                    function_path TEXT NOT NULL,
                    created_at timestamp WITH time zone NOT NULL,
                    updated_at timestamp WITH time zone NOT NULL,
                    started_at timestamp,
                    ended_at timestamp,
                    resolved_at timestamp,
                    failed_at timestamp,
                    parent_id character(32),
                    description TEXT,
                    tags TEXT NOT NULL,
                    source_code TEXT NOT NULL,
                    root_id character(32) NOT NULL,
                    nested_future_id character(32),
                    resource_requirements_json JSONB,
                    exception_metadata_json JSONB,
                    container_image_uri TEXT,
                    external_exception_metadata_json JSONB,
                    original_run_id character(32),
                    cache_key TEXT,
                    user_id character(32),
                    organization_id character(32),

                    PRIMARY KEY (id),

                    FOREIGN KEY(root_id) REFERENCES runs (id),
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (organization_id) REFERENCES organizations(id)
                );
            """,
        )
        execute_text(
            conn,
            """
            INSERT INTO runs_new
                SELECT
                    id,
                    future_state,
                    name,
                    function_path,
                    created_at,
                    updated_at,
                    started_at,
                    ended_at,
                    resolved_at,
                    failed_at,
                    parent_id,
                    description,
                    tags,
                    source_code,
                    root_id,
                    nested_future_id,
                    resource_requirements_json,
                    exception_metadata_json,
                    container_image_uri,
                    external_exception_metadata_json,
                    original_run_id,
                    cache_key,
                    user_id,
                    NULL
                FROM runs;
            """,
        )
        execute_text(conn, "DROP TABLE runs;")
        execute_text(conn, "ALTER TABLE runs_new RENAME TO runs;")
        execute_text(conn, "CREATE INDEX ix_runs_cache_key ON runs (cache_key);")
        execute_text(conn, "CREATE INDEX ix_runs_function_path ON runs (function_path);")

        execute_text(
            conn,
            """
            CREATE TABLE metric_labels_new (
                    metric_id TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_labels JSONB NOT NULL DEFAULT '{}',
                    metric_type SMALLINT NOT NULL,
                    organization_id character(32),

                    PRIMARY KEY (metric_id),

                    FOREIGN KEY (organization_id) REFERENCES organizations(id)
                );
            """,
        )
        execute_text(
            conn,
            """
            INSERT INTO metric_labels_new
                SELECT
                    metric_id,
                    metric_name,
                    metric_labels,
                    metric_type,
                    NULL
                FROM metric_labels;
            """,
        )
        execute_text(conn, "DROP TABLE metric_labels;")
        execute_text(conn, "ALTER TABLE metric_labels_new RENAME TO metric_labels;")
        execute_text(
            conn,
            "CREATE UNIQUE INDEX metric_labels_name_labels_idx "
            "ON metric_labels(metric_name, metric_labels);",
        )

        execute_text(
            conn,
            """
            CREATE TABLE artifacts_new (
                id character(40) NOT NULL,
                json_summary JSONB NOT NULL,
                created_at timestamp NOT NULL,
                updated_at timestamp NOT NULL,
                type_serialization JSONB NOT NULL,
                organization_id character(32),

                PRIMARY KEY (id),

                FOREIGN KEY (organization_id) REFERENCES organizations(id)
            );
            """,
        )
        execute_text(
            conn,
            """
            INSERT INTO artifacts_new
                SELECT
                    id,
                    json_summary,
                    created_at,
                    updated_at,
                    type_serialization,
                    NULL
                FROM artifacts;
            """,
        )
        execute_text(conn, "DROP TABLE artifacts;")
        execute_text(conn, "ALTER TABLE artifacts_new RENAME TO artifacts;")


def down_sqlite():
    reinstate_db_file_from_backup(suffix="0.32.0")


def up_postgres():
    with db().get_engine().begin() as conn:
        execute_text(
            conn,
            """
            ALTER TABLE resolutions ADD COLUMN organization_id character(32)
              REFERENCES organizations(id);
            ALTER TABLE runs ADD COLUMN organization_id character(32)
              REFERENCES organizations(id);
            ALTER TABLE metric_labels ADD COLUMN organization_id character(32)
              REFERENCES organizations(id);
            ALTER TABLE artifacts ADD COLUMN organization_id character(32)
              REFERENCES organizations(id);
            """,
        )


def down_postgres():
    with db().get_engine().begin() as conn:
        execute_text(
            conn,
            """
            ALTER TABLE resolutions DROP COLUMN organization_id;
            ALTER TABLE runs DROP COLUMN organization_id;
            ALTER TABLE metric_labels DROP COLUMN organization_id;
            ALTER TABLE artifacts DROP COLUMN organization_id;
            """,
        )


def execute_text(conn, statement):
    conn.execute(text(statement))


def up():
    if db().get_engine().url.drivername == "sqlite":
        up_sqlite()
    else:
        up_postgres()


def down():
    if db().get_engine().url.drivername == "sqlite":
        down_sqlite()
    else:
        down_postgres()
