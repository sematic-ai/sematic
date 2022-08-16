sematic_py_lib(
    name = "fixtures",
    srcs = ["fixtures.py"],
    data = [
        "//sematic/db:schema.sql.pg",
        "//sematic/db:schema.sql.sqlite",
    ],
    visibility = ["//visibility:public"],
    deps = [
        "//sematic:abstract_future",
        "//sematic/db:db",
        "//sematic/db:queries",
        "//sematic/db/models:factories",
        "//sematic/db/models:run",
    ],
    pip_deps = [
        "pytest",
        "testing.postgresql",
        "psycopg2-binary",
    ]
)

pytest_test(
    name = "test_db",
    srcs = ["test_db.py"],
    deps = [
        ":fixtures",
        "//sematic/db:queries",
        "//sematic/db/models:run",
    ],
)

pytest_test(
    name = "test_queries",
    srcs = ["test_queries.py"],
    deps = [
        ":fixtures",
        "//sematic:calculator",
        "//sematic/api/tests:fixtures",
        "//sematic/db:db",
        "//sematic/db:queries",
        "//sematic/db/models:artifact",
        "//sematic/db/models:edge",
        "//sematic/db/models:factories",
        "//sematic/db/models:run",
        "//sematic/types:init",
    ],
)

pytest_test(
    name = "test_migrate",
    srcs = ["test_migrate.py"],
    deps = [
        "//sematic/db:db",
        "//sematic/db:migrate_lib",
        "//sematic/db/tests:fixtures",
    ],
    pip_deps = ["sqlalchemy"],
)
