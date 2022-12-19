sematic_py_lib(
    name = "cloud_manager",
    srcs = ["cloud_manager.py"],
    deps = [
        "//sematic:api_client",
        "//sematic:external_resource",
        "//sematic/resolvers:abstract_resource_manager",
    ],
)


sematic_py_lib(
    name = "in_memory_manager",
    srcs = ["in_memory_manager.py"],
    deps = [
        "//sematic/resolvers:abstract_resource_manager",
        "//sematic:external_resource",
    ],
)