sematic_py_lib(
    name = "request_parameters",
    srcs = ["request_parameters.py"],
    pip_deps = [
        "sqlalchemy",
        "flask",
    ],
    deps = [],
)

sematic_py_lib(
    name = "storage",
    srcs = ["storage.py"],
    deps = [
        "//sematic:abstract_plugin",
        "//sematic/config:settings",
        "//sematic/plugins:abstract_storage",
        "//sematic/plugins/storage:local_storage",
    ]
)