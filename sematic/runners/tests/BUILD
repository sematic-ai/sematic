pytest_test(
    name = "test_local_runner",
    srcs = ["test_local_runner.py"],
    py_versions = [PY3.PY3_9, PY3.PY3_10, PY3.PY3_11],
    # buildifier: leave-alone
    deps = [
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
        "//sematic/resolvers/tests:fixtures",
        "//sematic/runners:local_runner",
        "//sematic/tests:fixtures",
        "//sematic/types:init",
        "//sematic/utils:exceptions",
    ],
)

pytest_test(
    name = "test_silent_runner",
    srcs = ["test_silent_runner.py"],
    deps = [
        "//sematic:abstract_function",
        "//sematic:function",
        "//sematic:future_context",
        "//sematic:retry_settings",
        "//sematic/plugins:abstract_external_resource",
        "//sematic/resolvers/tests:fixtures",
        "//sematic/runners:silent_runner",
        "//sematic/tests:utils",
        "//sematic/utils:exceptions",
    ],
)

pytest_test(
    name = "test_cloud_runner",
    srcs = ["test_cloud_runner.py"],
    py_versions = [PY3.PY3_9, PY3.PY3_10, PY3.PY3_11],
    deps = [
        "//sematic:api_client",
        "//sematic:function",
        "//sematic/api/tests:fixtures",
        "//sematic/db/models:factories",
        "//sematic/db/models:resolution",
        "//sematic/db/tests:fixtures",
        "//sematic/runners:cloud_runner",
        "//sematic/resolvers:resource_requirements",
        "//sematic/tests:fixtures",
        "//sematic/utils:env",
    ],
)
