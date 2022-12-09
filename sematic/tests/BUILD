load("//sematic:wheel_version.bzl", "wheel_version_string")

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
    name = "test_38_interpreter",
    srcs = ["test_38_interpreter.py"],
    pip_deps = ["requests"],
    py_versions = [PY3.PY38],
    deps = [],
)

pytest_test(
    name = "test_39_interpreter",
    srcs = ["test_39_interpreter.py"],
    pip_deps = ["requests"],
    py_versions = [PY3.PY39],
    deps = [],
)

pytest_test(
    name = "test_api_client",
    srcs = ["test_api_client.py"],
    deps = [
        "//sematic:api_client",
        "//sematic:versions",
        "//sematic/config:config",
        "//sematic/db/models:factories",
        "//sematic/tests:fixtures",
    ],
)

pytest_test(
    name = "test_external_resource",
    srcs = ["test_external_resource.py"],
    deps = [
        "//sematic:external_resource",
    ],
)

pytest_test(
    name = "test_future",
    srcs = ["test_future.py"],
    deps = [
        "//sematic:calculator",
    ],
)

pytest_test(
    name = "test_future_context",
    srcs = ["test_future_context.py"],
    deps = [
        "//sematic:future_context",
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
        "//sematic:storage",
        "//sematic/db:queries",
        "//sematic/db/tests:fixtures",
        "//sematic/resolvers:cloud_resolver",
        "//sematic/scheduling:external_job",
        "//sematic/tests:fixtures",
    ],
)

pytest_test(
    name = "test_versions",
    srcs = ["test_versions.py"],
    data = [
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

sematic_py_lib(
    name = "fixtures",
    srcs = ["fixtures.py"],
    deps = [
        "//sematic:api_client",
        "//sematic:storage",
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
        "//sematic/resolvers/tests:fixtures",
    ],
)
