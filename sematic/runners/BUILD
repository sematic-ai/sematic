sematic_py_lib(
    name = "local_runner",
    srcs = ["local_runner.py"],
    pip_deps = [
        "python-socketio",
        "websocket-client",
    ],
    # buildifier: leave-alone
    deps = [
        ":silent_runner",
        "//sematic:abstract_function",
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
        "//sematic/plugins:abstract_builder",
        "//sematic/resolvers:abstract_resource_manager",
        "//sematic/resolvers/resource_managers:server_manager",
        "//sematic/utils:exceptions",
        "//sematic/utils:git",
    ],
)

sematic_py_lib(
    name = "state_machine_runner",
    srcs = ["state_machine_runner.py"],
    deps = [
        "//sematic:abstract_function",
        "//sematic:abstract_future",
        "//sematic:runner",
        "//sematic/plugins:abstract_external_resource",
        "//sematic/resolvers:abstract_resource_manager",
        "//sematic/utils:exceptions",
        "//sematic/utils:signals",
        "//sematic/utils:timeout",
    ],
)

sematic_py_lib(
    name = "silent_runner",
    srcs = ["silent_runner.py"],
    deps = [
        "//sematic:abstract_future",
        "//sematic:future_context",
        "//sematic/plugins:abstract_external_resource",
        "//sematic/resolvers:abstract_resource_manager",
        "//sematic/resolvers/resource_managers:memory_manager",
        "//sematic/runners:state_machine_runner",
    ],
)

sematic_py_lib(
    name = "cloud_runner",
    srcs = ["cloud_runner.py"],
    pip_deps = [
        "cloudpickle",
    ],
    deps = [
        ":local_runner",
        "//sematic:abstract_future",
        "//sematic:api_client",
        "//sematic:container_images",
        "//sematic/db/models:artifact",
        "//sematic/db/models:edge",
        "//sematic/db/models:resolution",
        "//sematic/db/models:run",
        "//sematic:graph",
        "//sematic/plugins:abstract_external_resource",
        "//sematic/utils:exceptions",
        "//sematic/utils:memoized_property",
    ],
)
