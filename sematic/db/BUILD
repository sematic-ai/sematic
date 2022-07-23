sematic_py_lib(
    name = "db",
    srcs = ["db.py"],
    deps = [
        "//sematic:config",
        requirement("sqlalchemy"),
        requirement("psycopg2-binary"),
    ],
)

sematic_py_lib(
    name = "queries",
    srcs = ["queries.py"],
    deps = [
        ":db",
        "//sematic/db/models:artifact",
        "//sematic/db/models:edge",
        "//sematic/db/models:note",
        "//sematic/db/models:run",
        "//sematic/db/models:user",
        requirement("sqlalchemy"),
    ],
)

exports_files([
    "schema.sql.pg",
    "schema.sql.sqlite",
])

sematic_py_lib(
    name = "migrate_lib",
    srcs = ["migrate.py"],
    data = glob(["migrations/*.sql"]),
    deps = [
        "//sematic:config",
        "//sematic/db",
    ],
)

py_binary(
    name = "migrate",
    srcs = ["migrate.py"],
    deps = [":migrate_lib"],
)
