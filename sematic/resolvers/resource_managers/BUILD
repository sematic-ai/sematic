sematic_py_lib(
    name = "memory_manager",
    srcs = ["memory_manager.py"],
    deps = [
        "//sematic/resolvers:abstract_resource_manager",
        "//sematic/plugins:abstract_external_resource",
    ],
)

sematic_py_lib(
    name = "server_manager",
    srcs = ["server_manager.py"],
    deps = [
        "//sematic:api_client",
        "//sematic/plugins:abstract_external_resource",
        "//sematic/resolvers:abstract_resource_manager",
    ],
)
