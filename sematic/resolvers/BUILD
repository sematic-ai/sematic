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
    pip_deps = [
        "python-socketio",
        "websocket-client",
    ],
    # buildifier: leave-alone
    deps = [
        ":silent_resolver",
        "//sematic:abstract_calculator",
        "//sematic:abstract_future",
        "//sematic:api_client",
        "//sematic:graph",
        "//sematic:versions",
        "//sematic/caching:init",
        "//sematic/config:config",
        "//sematic/config:user_settings",
        "//sematic/db/models:artifact",
        "//sematic/db/models:edge",
        "//sematic/db/models:factories",
        "//sematic/db/models:run",
        "//sematic/resolvers:abstract_resource_manager",
        "//sematic/resolvers/resource_managers:server_manager",
        "//sematic/utils:exceptions",
        "//sematic/utils:git",
    ],
)

sematic_py_lib(
    name = "state_machine_resolver",
    srcs = ["state_machine_resolver.py"],
    deps = [
        "//sematic:abstract_calculator",
        "//sematic:abstract_future",
        "//sematic:resolver",
        "//sematic/plugins:abstract_external_resource",
        "//sematic/resolvers:abstract_resource_manager",
        "//sematic/utils:exceptions",
        "//sematic/utils:signals",
    ],
)

sematic_py_lib(
    name = "silent_resolver",
    srcs = ["silent_resolver.py"],
    deps = [
        "//sematic:abstract_future",
        "//sematic:future_context",
        "//sematic/plugins:abstract_external_resource",
        "//sematic/resolvers:abstract_resource_manager",
        "//sematic/resolvers:state_machine_resolver",
        "//sematic/resolvers/resource_managers:memory_manager",
    ],
)

sematic_py_lib(
    name = "cloud_resolver",
    srcs = ["cloud_resolver.py"],
    pip_deps = [
        "cloudpickle",
    ],
    deps = [
        ":local_resolver",
        "//sematic:abstract_future",
        "//sematic:api_client",
        "//sematic:container_images",
        "//sematic/db/models:artifact",
        "//sematic/db/models:edge",
        "//sematic/db/models:resolution",
        "//sematic/db/models:run",
        "//sematic/plugins:abstract_external_resource",
        "//sematic/utils:exceptions",
        "//sematic/utils:memoized_property",
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
        "//sematic:calculator",
        "//sematic:future",
        "//sematic:future_context",
        "//sematic:log_reader",
        "//sematic:versions",
        "//sematic/config:user_settings",
        "//sematic/db/models:artifact",
        "//sematic/db/models:edge",
        "//sematic/db/models:factories",
        "//sematic/resolvers:cloud_resolver",
        "//sematic/scheduling:job_details",
        "//sematic/utils:exceptions",
    ],
)

exports_files([
    "worker.py",
])
