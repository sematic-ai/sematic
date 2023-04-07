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
    name = "test_calculator",
    srcs = ["test_calculator.py"],
    deps = [
        "//sematic:abstract_calculator",
        "//sematic:calculator",
        "//sematic:future",
        "//sematic/db/tests:fixtures",
        "//sematic/utils:exceptions",
    ],
)

# <add python version>: A new test will need to be added when a python version is added
pytest_test(
    name = "test_3_8_interpreter",
    srcs = ["test_3_8_interpreter.py"],
    pip_deps = ["requests"],
    py_versions = [PY3.PY3_8],
    deps = [],
)

pytest_test(
    name = "test_3_9_interpreter",
    srcs = ["test_3_9_interpreter.py"],
    pip_deps = ["requests"],
    py_versions = [PY3.PY3_9],
    deps = [],
)

pytest_test(
    name = "test_3_10_interpreter",
    srcs = ["test_3_10_interpreter.py"],
    pip_deps = ["requests"],
    py_versions = [PY3.PY3_10],
    deps = [],
)

pytest_test(
    name = "test_3_10_calculator",
    srcs = ["test_3_10_calculator.py"],
    pip_deps = [],
    py_versions = [PY3.PY3_10],
    deps = [
        "//sematic:calculator",
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
        "//sematic/tests:fixtures",
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
        "//sematic:calculator",
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
        "//sematic/resolvers:cloud_resolver",
        "//sematic/scheduling:job_details",
        "//sematic/tests:fixtures",
    ],
)

pytest_test(
    name = "test_versions",
    srcs = ["test_versions.py"],
    data = [
        "//:docs/changelog.md",
        "//:helm/sematic-server/Chart.yaml",
        "//:README.md",
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
    deps = [
        "//sematic:abstract_future",
        "//sematic:api_client",
        "//sematic:calculator",
        "//sematic:graph",
        "//sematic/api/tests:fixtures",
        "//sematic/db/models:factories",
        "//sematic/db/tests:fixtures",
        "//sematic/resolvers:local_resolver",
    ],
)
