pytest_test(
    name = "test_local_resolver",
    srcs = ["test_local_resolver.py"],
    # buildifier: leave-alone
    deps = [
        ":fixtures",
        "//sematic:abstract_function",
        "//sematic:abstract_future",
        "//sematic:function",
        "//sematic:retry_settings",
        "//sematic/api/tests:fixtures",
        "//sematic/config/tests:fixtures",
        "//sematic/db:db",
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
        "//sematic:abstract_function",
        "//sematic:function",
        "//sematic:future_context",
        "//sematic:retry_settings",
        "//sematic/plugins:abstract_external_resource",
        "//sematic/resolvers:silent_resolver",
        "//sematic/resolvers/tests:fixtures",
        "//sematic/tests:utils",
        "//sematic/utils:exceptions",
    ],
)

pytest_test(
    name = "test_type_utils",
    srcs = ["test_type_utils.py"],
    deps = [
        "//sematic/resolvers:type_utils",
    ],
)

pytest_test(
    name = "test_cloud_resolver",
    srcs = ["test_cloud_resolver.py"],
    deps = [
        "//sematic:api_client",
        "//sematic:function",
        "//sematic/api/tests:fixtures",
        "//sematic/db/models:factories",
        "//sematic/db/models:resolution",
        "//sematic/db/tests:fixtures",
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
        "//sematic:api_client",
        "//sematic:function",
        "//sematic:future_context",
        "//sematic/api/tests:fixtures",
        "//sematic/config:user_settings",
        "//sematic/config/tests:fixtures",
        "//sematic/db:queries",
        "//sematic/db/models:edge",
        "//sematic/db/models:factories",
        "//sematic/db/models:resolution",
        "//sematic/db/tests:fixtures",
        "//sematic/resolvers:cloud_resolver",
        "//sematic/resolvers:worker",
        "//sematic/tests:fixtures",
        "//sematic/utils:stdout",
    ],
)

sematic_py_lib(
    name = "fixtures",
    srcs = ["fixtures.py"],
    deps = [
        "//sematic/plugins:abstract_external_resource",
    ],
)
