# flake8: noqa E501
# Standard Library
import logging

# Sematic
from sematic.db.db import db
from sematic.db.migration_utils import back_up_db_file, reinstate_db_file_from_backup

logger = logging.getLogger(__name__)


def sqlite_up():
    back_up_db_file("0.31.2")

    with db().get_engine().begin() as conn:
        conn.execute(
            "UPDATE runs SET function_path = 'UNKNOWN.UNKNOWN' WHERE function_path IS NULL;"
        )
        conn.execute("UPDATE runs SET tags = '[]' WHERE tags IS NULL;")
        conn.execute(
            "UPDATE runs SET source_code = 'source code unavailable' WHERE source_code IS NULL;"
        )
        conn.execute(
            "UPDATE jobs SET created_at = datetime(0, 'unixepoch') WHERE created_at IS NULL;"
        )
        conn.execute(
            "UPDATE jobs SET updated_at = datetime(0, 'unixepoch') WHERE updated_at IS NULL;"
        )
        conn.execute(
            "UPDATE notes SET created_at = datetime(0, 'unixepoch') WHERE created_at IS NULL;"
        )
        conn.execute(
            "UPDATE notes SET updated_at = datetime(0, 'unixepoch') WHERE updated_at IS NULL;"
        )

        conn.execute(
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

                PRIMARY KEY (id),

                FOREIGN KEY(root_id) REFERENCES runs (id),
                FOREIGN KEY(user_id) REFERENCES users (id)
            );
            """
        )

        conn.execute(
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
                    user_id
                FROM runs;
            """
        )

        conn.execute("DROP TABLE runs;")
        conn.execute("ALTER TABLE runs_new RENAME TO runs;")
        conn.execute("CREATE INDEX ix_runs_cache_key ON runs (cache_key);")
        conn.execute("CREATE INDEX ix_runs_function_path ON runs (function_path);")

        conn.execute(
            """
            CREATE TABLE artifacts_new (
                id character(40) NOT NULL,
                json_summary JSONB NOT NULL,
                created_at timestamp NOT NULL,
                updated_at timestamp NOT NULL,
                type_serialization JSONB NOT NULL,

                PRIMARY KEY (id)
            );
            """
        )
        conn.execute(
            """
            INSERT INTO artifacts_new
                SELECT
                    id,
                    json_summary,
                    created_at,
                    updated_at,
                    type_serialization
                FROM artifacts;
            """
        )
        conn.execute("DROP TABLE artifacts;")
        conn.execute("ALTER TABLE artifacts_new RENAME TO artifacts;")

        conn.execute(
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

                PRIMARY KEY (root_id),
                FOREIGN KEY (root_id) REFERENCES runs(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            """
        )

        conn.execute(
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
                    build_config
                FROM resolutions;
            """
        )
        conn.execute("DROP TABLE resolutions;")
        conn.execute("ALTER TABLE resolutions_new RENAME TO resolutions;")

        conn.execute(
            """
            CREATE TABLE jobs_new (
                name TEXT NOT NULL,
                namespace TEXT NOT NULL,
                run_id character(32) NOT NULL,
                last_updated_epoch_seconds double precision NOT NULL,
                state TEXT NOT NULL,
                kind TEXT NOT NULL,
                message TEXT NOT NULL,
                detail_serialization JSONB NOT NULL,
                status_history_serialization JSONB NOT NULL,
                created_at timestamp without time zone NOT NULL,
                updated_at timestamp without time zone NOT NULL,

                PRIMARY KEY(name, namespace),

                FOREIGN KEY(run_id) REFERENCES runs (id)
            );
            """
        )

        conn.execute(
            """
            INSERT INTO jobs_new
                SELECT
                    name,
                    namespace,
                    run_id,
                    last_updated_epoch_seconds,
                    state,
                    kind,
                    message,
                    detail_serialization,
                    status_history_serialization,
                    created_at,
                    updated_at
                FROM jobs;
            """
        )
        conn.execute("DROP TABLE jobs;")
        conn.execute("ALTER TABLE jobs_new RENAME TO jobs;")
        conn.execute("CREATE INDEX ix_jobs_run_id ON jobs (run_id);")

        conn.execute(
            """
            CREATE TABLE notes_new (
                id character(32) NOT NULL,
                user_id character(32),
                note TEXT NOT NULL,
                run_id character(32) NOT NULL,
                root_id character(32) NOT NULL,
                created_at timestamp without time zone NOT NULL,
                updated_at timestamp without time zone NOT NULL,

                PRIMARY KEY(id),

                FOREIGN KEY(run_id) REFERENCES runs (id),
                FOREIGN KEY(root_id) REFERENCES runs (id),
                FOREIGN KEY(user_id) REFERENCES users (id)
            );
            """
        )
        conn.execute(
            """
            INSERT INTO notes_new
                SELECT
                    id,
                    user_id,
                    note,
                    run_id,
                    root_id,
                    created_at,
                    updated_at
            FROM notes;
            """
        )
        conn.execute("DROP TABLE notes;")
        conn.execute("ALTER TABLE notes_new RENAME TO notes;")

        conn.execute(
            """
            CREATE TABLE edges_new (
                id character(32) NOT NULL,
                source_run_id character(32),
                source_name TEXT,
                destination_run_id character(32),
                destination_name TEXT,
                artifact_id character(40),
                parent_id character(32),
                created_at timestamp NOT NULL,
                updated_at timestamp NOT NULL,

                PRIMARY KEY (id),

                FOREIGN KEY(artifact_id) REFERENCES artifacts (id),
                FOREIGN KEY(parent_id) REFERENCES edges (id),
                FOREIGN KEY(destination_run_id) REFERENCES runs (id),
                FOREIGN KEY(source_run_id) REFERENCES runs (id)
            );
            """
        )
        conn.execute(
            """
            INSERT INTO edges_new
            SELECT
                id,
                source_run_id,
                source_name,
                destination_run_id,
                destination_name,
                artifact_id,
                parent_id,
                created_at,
                updated_at
            FROM edges;
            """
        )
        conn.execute("DROP TABLE edges;")
        conn.execute("ALTER TABLE edges_new RENAME TO edges;")
        conn.execute("CREATE INDEX ix_edges_source_run_id ON edges (source_run_id);")
        conn.execute(
            "CREATE INDEX ix_edges_destination_run_id ON edges (destination_run_id);"
        )

        conn.execute(
            """
            CREATE TABLE metric_values_new (
                metric_id TEXT NOT NULL,
                value FLOAT NOT NULL,
                metric_time TIMESTAMP NOT NULL,
                created_at TIMESTAMP NOT NULL,

                FOREIGN KEY(metric_id) REFERENCES metric_labels (metric_id)
            );
            """
        )
        conn.execute(
            """
            INSERT INTO metric_values_new
            SELECT
                metric_id,
                value,
                metric_time,
                created_at
            FROM metric_values;
            """
        )
        conn.execute("DROP TABLE metric_values;")
        conn.execute("ALTER TABLE metric_values_new RENAME TO metric_values;")
        conn.execute(
            "CREATE INDEX metric_values_id_time_idx ON metric_values (metric_id, metric_time DESC);"
        )
        conn.execute(
            "CREATE INDEX metric_values_time_idx ON metric_values (metric_time DESC);"
        )


def sqlite_down():
    reinstate_db_file_from_backup("0.31.2")


def postgres_up():
    with db().get_engine().begin() as conn:
        conn.execute(
            """
            UPDATE runs SET function_path = 'UNKNOWN.UNKNOWN' WHERE function_path IS NULL;
            UPDATE runs SET tags = '[]' WHERE tags IS NULL;
            UPDATE runs SET source_code = 'source code unavailable' WHERE source_code IS NULL;
            UPDATE jobs SET created_at = to_timestamp(0) WHERE created_at IS NULL;
            UPDATE jobs SET updated_at = to_timestamp(0) WHERE updated_at IS NULL;
            UPDATE notes SET created_at = to_timestamp(0) WHERE created_at IS NULL;
            UPDATE notes SET updated_at = to_timestamp(0) WHERE updated_at IS NULL;

            ALTER TABLE artifacts ALTER COLUMN type_serialization SET NOT NULL;
            ALTER TABLE jobs ALTER COLUMN created_at SET NOT NULL;
            ALTER TABLE jobs ALTER COLUMN updated_at SET NOT NULL;
            ALTER TABLE notes ALTER COLUMN created_at SET NOT NULL;
            ALTER TABLE notes ALTER COLUMN updated_at SET NOT NULL;
            ALTER TABLE runs ALTER COLUMN function_path SET NOT NULL;
            ALTER TABLE runs ALTER COLUMN root_id SET NOT NULL;
            ALTER TABLE runs ALTER COLUMN tags SET NOT NULL;
            ALTER TABLE runs ALTER COLUMN source_code SET NOT NULL;

            ALTER TABLE edges ADD CONSTRAINT edges_destination_run_id_fkey FOREIGN KEY (destination_run_id) REFERENCES runs(id);
            ALTER TABLE edges ADD CONSTRAINT edges_source_run_id_fkey FOREIGN KEY (source_run_id) REFERENCES runs(id);

            ALTER TABLE metric_values ADD CONSTRAINT metric_values_metric_id_fkey FOREIGN KEY (metric_id) REFERENCES metric_labels(metric_id);
            ALTER TABLE runs ADD CONSTRAINT runs_root_id_fkey FOREIGN KEY (root_id) REFERENCES runs(id);

            ALTER TABLE runs DROP COLUMN IF EXISTS exception;
            ALTER TABLE runs DROP COLUMN IF EXISTS external_jobs_json;

            ALTER TABLE resolutions DROP COLUMN IF EXISTS external_jobs_json;

            ALTER INDEX jobs_run_id RENAME TO ix_jobs_run_id;
            ALTER INDEX runs_cache_key_index RENAME TO ix_runs_cache_key;
            ALTER INDEX runs_calculator_path RENAME TO ix_runs_function_path;
            """
        )


def postgres_down():
    with db().get_engine().begin() as conn:
        conn.execute(
            """
            ALTER TABLE artifacts ALTER COLUMN type_serialization DROP NOT NULL;
            ALTER TABLE jobs ALTER COLUMN created_at DROP NOT NULL;
            ALTER TABLE jobs ALTER COLUMN updated_at DROP NOT NULL;
            ALTER TABLE notes ALTER COLUMN created_at DROP NOT NULL;
            ALTER TABLE notes ALTER COLUMN updated_at DROP NOT NULL;
            ALTER TABLE runs ALTER COLUMN function_path DROP NOT NULL;
            ALTER TABLE runs ALTER COLUMN root_id DROP NOT NULL;
            ALTER TABLE runs ALTER COLUMN tags DROP NOT NULL;
            ALTER TABLE runs ALTER COLUMN source_code DROP NOT NULL;

            ALTER TABLE edges DROP CONSTRAINT edges_destination_run_id_fkey;
            ALTER TABLE edges DROP CONSTRAINT edges_source_run_id_fkey;

            ALTER TABLE metric_values DROP CONSTRAINT metric_values_metric_id_fkey;
            ALTER TABLE runs DROP CONSTRAINT runs_root_id_fkey;

            ALTER TABLE runs ADD COLUMN exception TEXT;
            ALTER TABLE runs ADD COLUMN external_jobs_json JSONB;

            ALTER TABLE resolutions ADD COLUMN external_jobs_json JSONB;

            ALTER INDEX ix_jobs_run_id RENAME TO jobs_run_id;
            ALTER INDEX ix_runs_cache_key RENAME TO runs_cache_key_index;
            ALTER INDEX ix_runs_function_path RENAME TO runs_calculator_path;
            """
        )


def up():
    if db().get_engine().url.drivername == "sqlite":
        sqlite_up()
    else:
        postgres_up()


def down():
    if db().get_engine().url.drivername == "sqlite":
        sqlite_down()
    else:
        postgres_down()
