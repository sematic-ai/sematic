load("//sematic:wheel_constants.bzl", "wheel_version_string")

sematic_py_lib(
    name = "fixtures",
    srcs = ["fixtures.py"],
    deps = [
        "//sematic:abstract_future",
        "//sematic:api_client",
        "//sematic/plugins/storage:memory_storage",
    ],
)

sematic_py_lib(
    name = "utils",
    srcs = ["utils.py"],
    pip_deps = ["pytest"],
    deps = [],
)

pytest_test(
    name = "test_function",
    srcs = ["test_function.py"],
    deps = [
        "//sematic:abstract_function",
        "//sematic:function",
        "//sematic:future",
        "//sematic/db/tests:fixtures",
        "//sematic/utils:exceptions",
    ],
)

pytest_test(
    name = "test_3_10_function",
    srcs = ["test_3_10_function.py"],
    pip_deps = [],
    py_versions = [PY3.PY3_10],
    deps = [
        "//sematic:function",
    ],
)

pytest_test(
    name = "test_api_client",
    srcs = ["test_api_client.py"],
    # buildifier: leave-alone
    deps = [
        "//sematic:api_client",
        "//sematic:versions",
        "//sematic/config:config",
        "//sematic/api/tests:fixtures",
        "//sematic/db/tests:fixtures",
        "//sematic/db:db",
        "//sematic/db:queries",
        "//sematic/tests:fixtures",
        "//sematic/metrics:metric_point",
        "//sematic/metrics/tests:fixtures",
        "//sematic/plugins/metrics_storage/sql/models:metric_value",
    ],
)

pytest_test(
    name = "test_abstract_plugin",
    srcs = ["test_abstract_plugin.py"],
    deps = [
        "//sematic:abstract_plugin",
    ],
)

pytest_test(
    name = "test_future",
    srcs = ["test_future.py"],
    deps = [
        "//sematic:function",
        "//sematic/resolvers:resource_requirements",
    ],
)

pytest_test(
    name = "test_init",
    srcs = ["test_init.py"],
    deps = [
        "//sematic:init",
    ],
)

pytest_test(
    name = "test_client",
    srcs = ["test_client.py"],
    deps = [
        "//sematic:client",
    ],
)

pytest_test(
    name = "test_log_reader",
    srcs = ["test_log_reader.py"],
    deps = [
        "//sematic:abstract_future",
        "//sematic:log_reader",
        "//sematic/api/tests:fixtures",
        "//sematic/db:queries",
        "//sematic/db/tests:fixtures",
        "//sematic/runners:cloud_runner",
        "//sematic/scheduling:job_details",
        "//sematic/tests:fixtures",
    ],
)

pytest_test(
    name = "test_versions",
    srcs = ["test_versions.py"],
    data = [
        "//:README.md",
        "//:docs/changelog.md",
        "//:helm/sematic-server/Chart.yaml",
    ],
    env = {"BAZEL_WHEEL_VERSION": wheel_version_string},
    pip_deps = [
        "pyyaml",
    ],
    deps = [
        "//sematic:versions",
    ],
)

pytest_test(
    name = "test_retry_settings",
    srcs = ["test_retry_settings.py"],
    deps = [
        "//sematic:retry_settings",
        "//sematic/utils:exceptions",
    ],
)

pytest_test(
    name = "test_graph",
    srcs = ["test_graph.py"],
    py_versions = [PY3.PY3_9, PY3.PY3_10, PY3.PY3_11],
    deps = [
        "//sematic:abstract_future",
        "//sematic:api_client",
        "//sematic:function",
        "//sematic:graph",
        "//sematic/api/tests:fixtures",
        "//sematic/db/models:factories",
        "//sematic/db/tests:fixtures",
        "//sematic/resolvers:local_resolver",
    ],
)

pytest_test(
    name = "test_abstract_system_metric",
    srcs = ["test_abstract_system_metric.py"],
    pip_deps = ["sqlalchemy"],
    # buildifier: leave-alone
    deps = [
        "//sematic:abstract_future",
        "//sematic:abstract_system_metric",
        "//sematic/db:db",
        "//sematic/db/models:run",
        "//sematic/db/tests:fixtures",
        "//sematic/metrics/tests:fixtures",
        "//sematic/metrics:metric_point",
        "//sematic/utils:exceptions",
    ],
)
