
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
    name = "test_type_utils",
    srcs = ["test_type_utils.py"],
    deps = [
        "//sematic/resolvers:type_utils",
    ],
)

pytest_test(
    name = "test_worker",
    srcs = ["test_worker.py"],
    py_versions = [PY3.PY3_9, PY3.PY3_10, PY3.PY3_11],
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
        "//sematic/utils:env",
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
