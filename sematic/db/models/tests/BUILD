pytest_test(
    name = "test_job",
    srcs = ["test_job.py"],
    deps = [
        "//sematic/db/models:factories",
        "//sematic/scheduling:job_details",
        "//sematic/utils:exceptions",
    ],
)

pytest_test(
    name = "test_factories",
    srcs = ["test_factories.py"],
    deps = [
        "//sematic:abstract_future",
        "//sematic:calculator",
        "//sematic/db/models:edge",
        "//sematic/db/models:factories",
        "//sematic/db/models:job",
        "//sematic/db/models:resolution",
        "//sematic/db/models:run",
        "//sematic/db/tests:fixtures",
        "//sematic/resolvers:resource_requirements",
        "//sematic/scheduling:job_details",
        "//sematic/types:serialization",
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
