sematic_py_lib(
    name = "db",
    srcs = ["db.py"],
    deps = [
        "//sematic:config",
        requirement("sqlalchemy"),
        requirement("psycopg2-binary")
    ]
)

sematic_py_lib(
    name = "queries",
    srcs = ["queries.py"],
    deps = [
        ":db",
        "//sematic/db/models:artifact",
        "//sematic/db/models:edge",
        "//sematic/db/models:run",
        requirement("sqlalchemy"),

    ]
)

exports_files(["schema.sql"])
