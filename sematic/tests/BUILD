load("//sematic:wheel_version.bzl", "wheel_version_string")

pytest_test(
    name = "test_calculator",
    srcs = ["test_calculator.py"],
    deps = [
        "//sematic:abstract_calculator",
        "//sematic:calculator",
        "//sematic:future",
        "//sematic/db/tests:fixtures",
    ],
)

pytest_test(
    name = "test_config_dir",
    srcs = ["test_config_dir.py"],
    deps = [
        "//sematic:config_dir",
        "//sematic/tests:fixtures",
    ],
)

# <add python version>: A new test will need to be added when a python version is added
pytest_test(
    name = "test_38_interpreter",
    srcs = ["test_38_interpreter.py"],
    deps = [],
    pip_deps = ["requests"],
    py_versions=[PY3.PY38],
)

pytest_test(
    name = "test_39_interpreter",
    srcs = ["test_39_interpreter.py"],
    deps = [],
    pip_deps = ["requests"],
    py_versions=[PY3.PY39],
)

pytest_test(
    name = "test_api_client",
    srcs = ["test_api_client.py"],
    deps = [
        "//sematic:api_client",
        "//sematic:config",
        "//sematic:versions",
        "//sematic/db/models:factories",
        "//sematic/tests:fixtures",
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
        "//sematic/tests:fixtures",
        "//sematic/db/tests:fixtures",
        "//sematic/resolvers:cloud_resolver",
        "//sematic/scheduling:external_job",
    ],
)

pytest_test(
    name = "test_user_settings",
    srcs = ["test_user_settings.py"],
    deps = [
        "//sematic:config",
        "//sematic:user_settings",
    ],
)

pytest_test(
    name = "test_versions",
    srcs = ["test_versions.py"],
    deps = [
        "//sematic:versions",
    ],
    pip_deps = [
        "pyyaml",
    ],
    data = [
        "//:docs/changelog.md",
        "//:helm/sematic/values.yaml",
    ],
    env = {"BAZEL_WHEEL_VERSION": wheel_version_string},
)

sematic_py_lib(
    name = "fixtures",
    srcs = ["fixtures.py"],
    deps = [
        "//sematic:api_client",
        "//sematic:storage",
    ],
)
