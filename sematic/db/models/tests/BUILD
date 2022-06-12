pytest_test(
    name = "test_factories",
    srcs = ["test_factories.py"],
    deps = [
        "//sematic:abstract_future",
        "//sematic:calculator",
        "//sematic/db/models:factories",
    ]
)

pytest_test(
    name = "test_run",
    srcs = ["test_run.py"],
    deps = [
        "//sematic:abstract_future",
        "//sematic/db/models:run",
    ]
)

pytest_test(
    name = "test_json_encodable_mixin",
    srcs = ["test_json_encodable_mixin.py"],
    deps = [
        "//sematic/db/tests:fixtures",
        "//sematic/db/models:run",
    ]
)