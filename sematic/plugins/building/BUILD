sematic_py_lib(
    name = "docker_client_utils",
    srcs = ["docker_client_utils.py"],
    pip_deps = [],
    deps = [],
)

sematic_py_lib(
    name = "docker_builder",
    srcs = ["docker_builder.py"],
    pip_deps = [
        "docker",
        "pyyaml",
    ],
    deps = [
        ":docker_client_utils",
        "//sematic:abstract_plugin",
        "//sematic:container_images",
        "//sematic/plugins:abstract_builder",
        "//sematic/utils:env",
        "//sematic/utils:types",
    ],
)
