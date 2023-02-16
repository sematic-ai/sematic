sematic_py_lib(
    name = "abstract_external_resource",
    srcs = ["abstract_external_resource.py"],
    deps = [
        "//sematic:abstract_future",
        "//sematic:abstract_plugin",
        "//sematic:future_context",
        "//sematic/utils:exceptions",
    ],
)

sematic_py_lib(
    name = "abstract_kuberay_wrapper",
    srcs = ["abstract_kuberay_wrapper.py"],
    deps = [],
)

sematic_py_lib(
    name = "abstract_storage",
    srcs = ["abstract_storage.py"],
    deps = [
        "//sematic:abstract_plugin",
        "//sematic/config:settings",
        "//sematic/db/models:user",
        "//sematic/utils:exceptions",
    ],
)

sematic_py_lib(
    name = "abstract_publisher",
    srcs = ["abstract_publisher.py"],
    deps = [
        "//sematic:abstract_plugin",
        "//sematic/config:settings",
    ],
)

sematic_py_lib(
    name = "abstract_auth",
    srcs = ["abstract_auth.py"],
    pip_deps = ["sqlalchemy"],
    deps = [
        "//sematic:abstract_plugin",
        "//sematic/config:server_settings",
        "//sematic/config:settings",
        "//sematic/db:queries",
        "//sematic/db/models:factories",
        "//sematic/db/models:user",
    ],
)
