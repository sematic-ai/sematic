pytest_test(
    name = "test_factories",
    srcs = ["test_factories.py"],
    deps = [
        "//sematic:abstract_future",
        "//sematic:calculator",
        "//sematic:storage",
        "//sematic/db/models:factories",
        "//sematic/tests:fixtures",
    ],
)

pytest_test(
    name = "test_resolution",
    srcs = ["test_resolution.py"],
    deps = [
        "//sematic/db/models:resolution",
        "//sematic/db/tests:fixtures",
    ],
)

pytest_test(
    name = "test_run",
    srcs = ["test_run.py"],
    deps = [
        "//sematic:abstract_future",
        "//sematic/db/models:run",
        "//sematic/scheduling:external_job",
    ],
)

pytest_test(
    name = "test_json_encodable_mixin",
    srcs = ["test_json_encodable_mixin.py"],
    deps = [
        "//sematic/db/models:run",
        "//sematic/db/tests:fixtures",
    ],
)
