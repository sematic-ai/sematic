sematic_py_lib(
    name = "local_resolver",
    srcs = ["local_resolver.py"],
    deps = [
        ":silent_resolver",
        "//sematic:abstract_calculator",
        "//sematic:abstract_future",
        "//sematic:api_client",
        "//sematic:config",
        "//sematic/db/models:artifact",
        "//sematic/db/models:edge",
        "//sematic/db/models:factories",
        "//sematic/db/models:run",
        "//sematic/utils:exceptions",
    ],
)

sematic_py_lib(
    name = "state_machine_resolver",
    srcs = ["state_machine_resolver.py"],
    deps = [
        "//sematic:abstract_calculator",
        "//sematic:abstract_future",
        "//sematic:resolver",
    ],
)

sematic_py_lib(
    name = "silent_resolver",
    srcs = ["silent_resolver.py"],
    deps = [
        "//sematic:abstract_future",
        "//sematic/resolvers:state_machine_resolver",
    ],
)

sematic_py_lib(
    name = "cloud_resolver",
    srcs = ["cloud_resolver.py"],
    deps = [
        ":local_resolver",
        "//sematic:abstract_future",
        "//sematic/db/models:artifact",
        "//sematic/db/models:edge",
        "//sematic/db/models:resolution",
        "//sematic/db/models:run",
        "//sematic:container_images",
        "//sematic/utils:exceptions",
    ],
    pip_deps = [
        "cloudpickle",
    ],
)

sematic_py_lib(
    name = "log_streamer",
    srcs = ["log_streamer.py"],
    deps = [
        "//sematic:storage",
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
    deps = [
        ":log_streamer",
        "//sematic:abstract_future",
        "//sematic:api_client",
        "//sematic:calculator",
        "//sematic:future",
        "//sematic/db/models:artifact",
        "//sematic/db/models:edge",
        "//sematic/db/models:factories",
        "//sematic/resolvers:cloud_resolver",
        "//sematic/utils:exceptions",
        "//sematic/utils:stdout",
    ],
    pip_deps = [
        "cloudpickle",
    ],
)

exports_files([
    "worker.py",
])
