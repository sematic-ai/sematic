pytest_test(
    name = "test_local_resolver",
    srcs = ["test_local_resolver.py"],
    deps = [
        "//sematic:abstract_future",
        "//sematic:calculator",
        "//sematic/types:init",
        "//sematic/db/models:edge",
        "//sematic/db/tests:fixtures",
        "//sematic/resolvers:local_resolver",
        "//sematic/api/tests:fixtures"
    ]
)

pytest_test(
    name = "test_silent_resolver",
    srcs = ["test_silent_resolver.py"],
    deps = [
        "//sematic/resolvers:silent_resolver",
        "//sematic:calculator",
    ]
)

pytest_test(
    name = "test_cloud_resolver",
    srcs = ["test_cloud_resolver.py"],
    deps = [
        "//sematic:calculator",
        "//sematic/resolvers:cloud_resolver",
        "//sematic/api/tests:fixtures",
        "//sematic/db/tests:fixtures",
        "//sematic/tests:fixtures",
        "//sematic:api_client",
    ]
)

pytest_test(
    name = "test_worker",
    srcs = ["test_worker.py"],
    deps = [
        "//sematic/resolvers:cloud_resolver",
        "//sematic/resolvers:worker",
        "//sematic:calculator",
        "//sematic/api/tests:fixtures",
        "//sematic/db/tests:fixtures",
        "//sematic/tests:fixtures",
        "//sematic:api_client",
    ]
)