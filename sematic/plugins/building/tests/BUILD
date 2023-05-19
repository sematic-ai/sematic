pytest_test(
    name = "test_docker_builder",
    srcs = ["test_docker_builder.py", "test_docker_client_utils.py"],
    data = glob([
        "fixtures/**",
    ]),
    pip_deps = ["docker"],
    deps = [
        "//sematic/config:settings",
        "//sematic/plugins/building:docker_builder",
        "//sematic/tests:utils",
    ],
)
