sematic_py_lib(
    name = "db",
    srcs = ["db.py"],
    pip_deps = [
        "sqlalchemy",
        "psycopg2-binary",
    ],
    deps = [
        "//sematic:config",
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
        "//sematic/db/models:note",
        "//sematic/db/models:resolution",
        "//sematic/db/models:run",
        "//sematic/db/models:user",
        "//sematic/scheduling:external_job",
    ],
)

exports_files(
    [
        "schema.sql.pg",
        "schema.sql.sqlite",
    ],
)

sematic_py_lib(
    name = "migrate_lib",
    srcs = ["migrate.py"],
    data = glob([
        "migrations/*.sql",
        "migrations/*.py",
    ]),
    pip_deps = [
        "click",
    ],
    deps = [
        "//sematic:config",
        "//sematic/db",
        "//sematic/db/models:artifact",
        "//sematic/db/models:edge",
        "//sematic/db/models:note",
        "//sematic/db/models:resolution",
        "//sematic/db/models:run",
        "//sematic/db/models:user",
    ],
)

py_binary(
    name = "migrate",
    srcs = ["migrate.py"],
    deps = [":migrate_lib"],
)
