sematic_py_lib(
    name = "fixtures",
    srcs = ["fixtures.py"],
    data = [
        "//sematic/db:schema.sql.sqlite",
    ],
    pip_deps = [
        "pytest",
        "testing.postgresql",
        "psycopg2-binary",
    ],
    # buildifier: leave-alone
    deps = [
        "//sematic:abstract_future",
        "//sematic/db:db",
        "//sematic/db:queries",
        "//sematic/db/models:factories",
        "//sematic/db/models:resolution",
        "//sematic/db/models:run",
        "//sematic/tests:fixtures",
    ],
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
    # buildifier: leave-alone
    deps = [
        ":fixtures",
        "//sematic:calculator",
        "//sematic:external_resource",
        "//sematic/api/tests:fixtures",
        "//sematic/db:db",
        "//sematic/db:queries",
        "//sematic/db/models:artifact",
        "//sematic/db/models:edge",
        "//sematic/db/models:external_resource_record",
        "//sematic/db/models:factories",
        "//sematic/db/models:resolution",
        "//sematic/db/models:run",
        "//sematic/resolvers/tests:fixtures",
        "//sematic/tests:fixtures",
        "//sematic/types:init",
    ],
)

pytest_test(
    name = "test_migrate",
    srcs = ["test_migrate.py"],
    pip_deps = ["sqlalchemy"],
    # buildifier: leave-alone
    deps = [
        "//sematic/db:db",
        "//sematic/db:migrate_lib",
        "//sematic/db/tests:fixtures",
    ],
)
