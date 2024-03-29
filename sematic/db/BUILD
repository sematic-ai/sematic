sematic_py_lib(
    name = "db",
    srcs = ["db.py"],
    pip_deps = [
        "sqlalchemy",
        "psycopg2-binary",
    ],
    # buildifier: leave-alone
    deps = [
        "//sematic/config:config",
    ],
)

sematic_py_lib(
    name = "queries",
    srcs = ["queries.py"],
    pip_deps = [
        "sqlalchemy",
    ],
    deps = [
        ":db",
        "//sematic/db/models:artifact",
        "//sematic/db/models:edge",
        "//sematic/db/models:external_resource",
        "//sematic/db/models:factories",
        "//sematic/db/models:job",
        "//sematic/db/models:note",
        "//sematic/db/models:organization",
        "//sematic/db/models:resolution",
        "//sematic/db/models:run",
        "//sematic/db/models:runs_external_resource",
        "//sematic/db/models:user",
        "//sematic/plugins:abstract_external_resource",
        "//sematic/utils:exceptions",
    ],
)

exports_files(
    [
        "schema.sql.sqlite",
    ],
)

sematic_py_lib(
    name = "migrate_lib",
    srcs = ["migrate.py", "migration_utils.py"],
    data = glob(
        [
            "migrations/*.sql",
            "migrations/*.py",
        ],
    ),
    pip_deps = [
        "click",
        "sqlalchemy",
    ],
    # buildifier: leave-alone
    deps = [
        # DO NOT add any other dependencies
        # or it may break the sequence of migrations
        # Migrations are written at a specific point in time, whereas the
        # codebase evolves.
        ":db",
        "//sematic/config:config",
    ],
)

py_binary(
    name = "migrate",
    srcs = ["migrate.py"],
    deps = [":migrate_lib"],
)
