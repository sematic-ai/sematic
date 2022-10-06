pytest_test(
    name = "test_local_resolver",
    srcs = ["test_local_resolver.py"],
    deps = [
        "//sematic:abstract_future",
        "//sematic:calculator",
        "//sematic/api/tests:fixtures",
        "//sematic/db/models:edge",
        "//sematic/db/models:resolution",
        "//sematic/db/tests:fixtures",
        "//sematic/tests:fixtures",
        "//sematic/resolvers:local_resolver",
        "//sematic/types:init",
    ],
)

pytest_test(
    name = "test_log_streamer",
    srcs = ["test_log_streamer.py"],
    deps = [
        "//sematic/resolvers:log_streamer",
        "//sematic/utils:retry",
    ],
)

pytest_test(
    name = "test_silent_resolver",
    srcs = ["test_silent_resolver.py"],
    deps = [
        "//sematic:calculator",
        "//sematic:future_context",
        "//sematic/resolvers:silent_resolver",
    ],
)

pytest_test(
    name = "test_cloud_resolver",
    srcs = ["test_cloud_resolver.py"],
    deps = [
        "//sematic:api_client",
        "//sematic:calculator",
        "//sematic/api/tests:fixtures",
        "//sematic/db/tests:fixtures",
        "//sematic/db/models:resolution",
        "//sematic/resolvers:cloud_resolver",
        "//sematic/resolvers:resource_requirements",
        "//sematic/tests:fixtures",
    ],
)

pytest_test(
    name = "test_worker",
    srcs = ["test_worker.py"],
    deps = [
        "//sematic:abstract_future",
        "//sematic:calculator",
        "//sematic/api/tests:fixtures",
        "//sematic/db:queries",
        "//sematic/db/tests:fixtures",
        "//sematic/db/models:resolution",
        "//sematic/resolvers:cloud_resolver",
        "//sematic/resolvers:worker",
        "//sematic/tests:fixtures",
    ],
)
