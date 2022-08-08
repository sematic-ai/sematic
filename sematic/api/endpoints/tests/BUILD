pytest_test(
    name = "test_runs",
    srcs = ["test_runs.py"],
    deps = [
        "//sematic:calculator",
        "//sematic/api/tests:fixtures",
        "//sematic/db:queries",
        "//sematic/db/tests:fixtures",
        requirement("flask"),
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
        requirement("flask"),
        requirement("sqlalchemy"),
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
        requirement("flask"),
    ],
)

pytest_test(
    name = "test_meta",
    srcs = ["test_meta.py"],
    deps = [
        "//sematic/api/endpoints:meta",
        "//sematic/api:app",
        "//sematic:user_settings",
        "//sematic:versions",
        "//sematic/api/tests:fixtures",
        requirement("flask"),
    ],
)
