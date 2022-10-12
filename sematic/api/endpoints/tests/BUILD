pytest_test(
    name = "test_resolutions",
    srcs = ["test_resolutions.py"],
    pip_deps = [
        "flask",
    ],
    deps = [
        "//sematic:abstract_future",
        "//sematic/api/tests:fixtures",
        "//sematic/db:queries",
        "//sematic/db/models:resolution",
        "//sematic/db/models:run",
        "//sematic/db/tests:fixtures",
        "//sematic/scheduling:external_job",
        "//sematic/scheduling:kubernetes",
    ],
)

pytest_test(
    name = "test_runs",
    srcs = ["test_runs.py"],
    pip_deps = [
        "flask",
    ],
    deps = [
        "//sematic:calculator",
        "//sematic/api/tests:fixtures",
        "//sematic/db:queries",
        "//sematic/db/tests:fixtures",
        "//sematic/tests:fixtures",
        "//sematic/utils:exceptions",
    ],
)

pytest_test(
    name = "test_notes",
    srcs = ["test_notes.py"],
    pip_deps = [
        "flask",
        "sqlalchemy",
    ],
    deps = [
        "//sematic/api/tests:fixtures",
        "//sematic/db:queries",
        "//sematic/db/models:note",
        "//sematic/db/models:run",
        "//sematic/db/models:user",
        "//sematic/db/tests:fixtures",
    ],
)

pytest_test(
    name = "test_auth",
    srcs = ["test_auth.py"],
    pip_deps = [
        "flask",
    ],
    deps = [
        "//sematic/api/endpoints:auth",
        "//sematic/api/tests:fixtures",
        "//sematic/db:queries",
        "//sematic/db/models:json_encodable_mixin",
        "//sematic/db/models:user",
    ],
)

pytest_test(
    name = "test_meta",
    srcs = ["test_meta.py"],
    pip_deps = [
        "flask",
    ],
    deps = [
        "//sematic:user_settings",
        "//sematic:versions",
        "//sematic/api:app",
        "//sematic/api/endpoints:meta",
        "//sematic/api/tests:fixtures",
    ],
)

pytest_test(
    name = "test_artifacts",
    srcs = ["test_artifacts.py"],
    pip_deps = [
        "flask",
    ],
    deps = [
        "//sematic/api/tests:fixtures",
        "//sematic/db/models:artifact",
        "//sematic/db/tests:fixtures",
        "//sematic/tests:fixtures",
    ],
)
