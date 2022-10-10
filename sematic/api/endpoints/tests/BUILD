pytest_test(
    name = "test_resolutions",
    srcs = ["test_resolutions.py"],
    deps = [
        "//sematic/api/tests:fixtures",
        "//sematic/db/models:resolution",
        "//sematic/db:queries",
        "//sematic/db/tests:fixtures",
        "//sematic/scheduling:external_job",
        "//sematic/scheduling:kubernetes",
    ],
    pip_deps = [
        "flask"
    ],
)

pytest_test(
    name = "test_runs",
    srcs = ["test_runs.py"],
    deps = [
        "//sematic:calculator",
        "//sematic/api/tests:fixtures",
        "//sematic/db:queries",
        "//sematic/db/tests:fixtures",
        "//sematic/tests:fixtures",
        "//sematic/utils:exceptions",
    ],
    pip_deps = [
        "flask"
    ],
)

pytest_test(
    name = "test_notes",
    srcs = ["test_notes.py"],
    deps = [
        "//sematic/api/tests:fixtures",
        "//sematic/db:queries",
        "//sematic/db/models:note",
        "//sematic/db/models:run",
        "//sematic/db/models:user",
        "//sematic/db/tests:fixtures",
    ],
    pip_deps = [
        "flask",
        "sqlalchemy",
    ],
)

pytest_test(
    name = "test_auth",
    srcs = ["test_auth.py"],
    deps = [
        "//sematic/api/endpoints:auth",
        "//sematic/api/tests:fixtures",
        "//sematic/db:queries",
        "//sematic/db/models:json_encodable_mixin",
        "//sematic/db/models:user",
    ],
    pip_deps = [
        "flask",
    ],
)

pytest_test(
    name = "test_meta",
    srcs = ["test_meta.py"],
    deps = [
        "//sematic:user_settings",
        "//sematic:versions",
        "//sematic/api:app",
        "//sematic/api/endpoints:meta",
        "//sematic/api/tests:fixtures",
    ],
    pip_deps = [
        "flask",
    ],
)

pytest_test(
    name = "test_artifacts",
    srcs = ["test_artifacts.py"],
    deps = [
        "//sematic/api/tests:fixtures",
        "//sematic/db/models:artifact",
        "//sematic/db/tests:fixtures",
        "//sematic/tests:fixtures",
    ],
    pip_deps = [
        "flask",
    ]
)
