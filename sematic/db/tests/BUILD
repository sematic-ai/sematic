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
        "//sematic:function",
        "//sematic/db:db",
        "//sematic/db:queries",
        "//sematic/db/models:edge",
        "//sematic/db/models:external_resource",
        "//sematic/db/models:factories",
        "//sematic/db/models:job",
        "//sematic/db/models:organization",
        "//sematic/db/models:organization_user",
        "//sematic/db/models:resolution",
        "//sematic/db/models:run",
        "//sematic/db/models:user",
        "//sematic/plugins:abstract_external_resource",
        "//sematic/scheduling:job_details",
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
    py_versions = [PY3.PY3_9, PY3.PY3_10, PY3.PY3_11],
    # buildifier: leave-alone
    deps = [
        ":fixtures",
        "//sematic:abstract_future",
        "//sematic:function",
        "//sematic/api/tests:fixtures",
        "//sematic/db:db",
        "//sematic/db:queries",
        "//sematic/db/models:artifact",
        "//sematic/db/models:external_resource",
        "//sematic/db/models:factories",
        "//sematic/db/models:resolution",
        "//sematic/db/models:run",
        "//sematic/plugins:abstract_external_resource",
        "//sematic/resolvers/tests:fixtures",
        "//sematic/scheduling:job_details",
        "//sematic/tests:fixtures",
        "//sematic/types:init",
        "//sematic/utils:exceptions",
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
