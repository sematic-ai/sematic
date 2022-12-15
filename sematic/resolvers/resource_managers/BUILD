sematic_py_lib(
    name = "init",
    srcs = ["__init__.py"],
    deps = [
        ":in_memory_manager",
        ":resource_manager",
    ],
)

sematic_py_lib(
    name = "in_memory_manager",
    srcs = ["in_memory_manager.py"],
    deps = [
        ":resource_manager",
        "//sematic:external_resource",
    ],
)

sematic_py_lib(
    name = "resource_manager",
    srcs = ["resource_manager.py"],
    deps = [
        "//sematic:external_resource",
    ],
)