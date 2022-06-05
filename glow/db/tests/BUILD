glow_py_lib(
    name = "fixtures",
    srcs = ["fixtures.py"],
    visibility = ["//visibility:public"],
    data = [
        "//glow/db:schema.sql",
    ],
    deps = [
        "//glow:abstract_future",
        "//glow/db:db",
        "//glow/db:queries",
        "//glow/db/models:run",
        requirement("pytest"),
        requirement("testing.postgresql"),
        requirement("psycopg2"),
    ]
)

pytest_test(
    name = "test_db",
    srcs = ["test_db.py"],
    deps = [
        ":fixtures",
        "//glow/db/models:run",
        "//glow/db:queries",
    ]
)

pytest_test(
    name = "test_queries",
    srcs = ["test_queries.py"],
    deps = [
        ":fixtures",
        "//glow/db:db",
        "//glow/types:init",
        "//glow/db:queries",
        "//glow/db/models:factories",
        "//glow/db/models:artifact",
        "//glow/db/models:run",
        "//glow/db/models:edge",
    ]
)