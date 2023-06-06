sematic_py_lib(
    name = "docker_client_utils",
    srcs = ["docker_client_utils.py"],
    pip_deps = [],
    deps = [],
)

sematic_py_lib(
    name = "docker_builder_config",
    srcs = ["docker_builder_config.py"],
    pip_deps = ["pyyaml"],
    deps = [
        "//sematic/plugins:abstract_builder",
        "//sematic/utils:types",
    ],
)

sematic_py_lib(
    name = "docker_builder",
    srcs = ["docker_builder.py"],
    pip_deps = [
        "docker",
    ],
    deps = [
        ":docker_builder_config",
        ":docker_client_utils",
        "//sematic:abstract_plugin",
        "//sematic:container_images",
        "//sematic/plugins:abstract_builder",
        "//sematic/utils:env",
        "//sematic/utils:spinner",
    ],
)
