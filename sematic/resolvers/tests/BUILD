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