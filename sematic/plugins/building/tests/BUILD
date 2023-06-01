sematic_py_lib(
    name = "config_lib",
    srcs = ["test_docker_builder_config.py"],
    data = ["fixtures"],
    pip_deps = [],
    deps = [
        "//sematic/plugins/building:docker_builder_config",
    ],
)

pytest_test(
    name = "test_docker_client_utils",
    srcs = ["test_docker_client_utils.py"],
    data = ["fixtures"],
    pip_deps = ["docker"],
    deps = [
        "//sematic/plugins/building:docker_client_utils",
    ],
)

pytest_test(
    name = "test_docker_builder_config",
    srcs = ["test_docker_builder_config.py"],
    data = ["fixtures"],
    pip_deps = [],
    deps = [
        ":config_lib",
    ],
)

pytest_test(
    name = "test_docker_builder",
    srcs = ["test_docker_builder.py"],
    data = ["fixtures"],
    pip_deps = ["docker"],
    deps = [
        ":config_lib",
        "//sematic/config:settings",
        "//sematic/plugins/building:docker_builder",
        "//sematic/tests:utils",
    ],
)
