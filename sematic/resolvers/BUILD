sematic_py_lib(
    name = "abstract_resource_manager",
    srcs = ["abstract_resource_manager.py"],
    deps = [
        "//sematic/plugins:abstract_external_resource",
    ],
)

sematic_py_lib(
    name = "local_resolver",
    srcs = ["local_resolver.py"],
    pip_deps = [],
    # buildifier: leave-alone
    deps = [
        "//sematic:resolver",
        "//sematic/runners:local_runner",
    ],
)

sematic_py_lib(
    name = "silent_resolver",
    srcs = ["silent_resolver.py"],
    deps = [
        "//sematic:resolver",
        "//sematic/runners:silent_runner",
    ],
)

sematic_py_lib(
    name = "cloud_resolver",
    srcs = ["cloud_resolver.py"],
    pip_deps = [],
    deps = [
        "//sematic:resolver",
        "//sematic/runners:cloud_runner",
    ],
)

sematic_py_lib(
    name = "type_utils",
    srcs = ["type_utils.py"],
    deps = [
        "//sematic:abstract_future",
    ],
)

sematic_py_lib(
    name = "log_streamer",
    srcs = ["log_streamer.py"],
    # buildifier: leave-alone
    deps = [
        "//sematic:api_client",
        "//sematic/config:config",
        "//sematic/config:user_settings",
        "//sematic/utils:signals",
        "//sematic/utils:stdout",
    ],
)

sematic_py_lib(
    name = "resource_requirements",
    srcs = ["resource_requirements.py"],
    deps = [],
)

sematic_py_lib(
    name = "worker",
    srcs = ["worker.py"],
    pip_deps = [
        "cloudpickle",
    ],
    deps = [
        ":log_streamer",
        "//sematic:abstract_future",
        "//sematic:api_client",
        "//sematic:function",
        "//sematic:future",
        "//sematic:future_context",
        "//sematic:graph",
        "//sematic:log_reader",
        "//sematic:versions",
        "//sematic/config:user_settings",
        "//sematic/db/models:artifact",
        "//sematic/db/models:edge",
        "//sematic/db/models:factories",
        "//sematic/db/models:run",
        "//sematic/db/models:resolution",
        "//sematic/runners:cloud_runner",
        "//sematic/runners:local_runner",
        "//sematic/scheduling:job_details",
        "//sematic/utils:exceptions",
    ],
)

exports_files([
    "worker.py",
])
