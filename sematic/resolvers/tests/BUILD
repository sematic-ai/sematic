pytest_test(
    name = "test_local_resolver",
    srcs = ["test_local_resolver.py"],
    deps = [
        ":fixtures",
        "//sematic:abstract_calculator",
        "//sematic:abstract_future",
        "//sematic:calculator",
        "//sematic:retry_settings",
        "//sematic/api/tests:fixtures",
        "//sematic/db/models:edge",
        "//sematic/db/models:resolution",
        "//sematic/db/tests:fixtures",
        "//sematic/resolvers:local_resolver",
        "//sematic/tests:fixtures",
        "//sematic/types:init",
        "//sematic/utils:exceptions",
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
    name = "test_resource_requirements",
    srcs = ["test_resource_requirements.py"],
    deps = [
        "//sematic/resolvers:resource_requirements",
        "//sematic/types:serialization",
    ],
)

pytest_test(
    name = "test_silent_resolver",
    srcs = ["test_silent_resolver.py"],
    deps = [
        "//sematic:abstract_calculator",
        "//sematic:calculator",
        "//sematic:retry_settings",
        "//sematic/resolvers:silent_resolver",
        "//sematic/utils:exceptions",
    ],
)

pytest_test(
    name = "test_cloud_resolver",
    srcs = ["test_cloud_resolver.py"],
    deps = [
        ":fixtures",
        "//sematic:api_client",
        "//sematic:calculator",
        "//sematic/api/tests:fixtures",
        "//sematic/db/models:resolution",
        "//sematic/db/tests:fixtures",
        "//sematic/resolvers:cloud_resolver",
        "//sematic/resolvers:resource_requirements",
        "//sematic/tests:fixtures",
        "//sematic/db/models:factories",
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
        "//sematic/db/models:resolution",
        "//sematic/db/tests:fixtures",
        "//sematic/resolvers:cloud_resolver",
        "//sematic/resolvers:worker",
        "//sematic/tests:fixtures",
    ],
)

sematic_py_lib(
    name = "fixtures",
    srcs = ["fixtures.py"],
    pip_deps = [
        "pytest",
    ],
    deps = [
        "//sematic/tests:fixtures",
    ],
)
