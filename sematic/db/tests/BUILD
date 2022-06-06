sematic_py_lib(
    name = "fixtures",
    srcs = ["fixtures.py"],
    visibility = ["//visibility:public"],
    data = [
        "//sematic/db:schema.sql",
    ],
    deps = [
        "//sematic:abstract_future",
        "//sematic/db:db",
        "//sematic/db:queries",
        "//sematic/db/models:run",
        requirement("pytest"),
        requirement("testing.postgresql"),
        requirement("psycopg2-binary"),
    ]
)

pytest_test(
    name = "test_db",
    srcs = ["test_db.py"],
    deps = [
        ":fixtures",
        "//sematic/db/models:run",
        "//sematic/db:queries",
    ]
)

pytest_test(
    name = "test_queries",
    srcs = ["test_queries.py"],
    deps = [
        ":fixtures",
        "//sematic/db:db",
        "//sematic/types:init",
        "//sematic/db:queries",
        "//sematic/db/models:factories",
        "//sematic/db/models:artifact",
        "//sematic/db/models:run",
        "//sematic/db/models:edge",
    ]
)