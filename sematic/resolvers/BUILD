load("//tools:sematic_pipeline.bzl", "sematic_pipeline")

sematic_py_lib(
    name = "local_resolver",
    srcs = ["local_resolver.py"],
    deps = [
        ":silent_resolver",
        "//sematic:abstract_future",
        "//sematic:api_client",
        "//sematic:config",
        "//sematic/db/models:artifact",
        "//sematic/db/models:edge",
        "//sematic/db/models:factories",
        "//sematic/db/models:run",
    ],
)

sematic_py_lib(
    name = "state_machine_resolver",
    srcs = ["state_machine_resolver.py"],
    deps = [
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
        "//sematic/db/models:run",
        requirement("kubernetes"),
    ],
)

sematic_py_lib(
    name = "worker",
    srcs = ["worker.py"],
    deps = [
        "//sematic:abstract_future",
        "//sematic:api_client",
        "//sematic:future",
        "//sematic/db/models:artifact",
        "//sematic/db/models:edge",
        "//sematic/db/models:factories",
        "//sematic/resolvers:cloud_resolver",
    ],
)

exports_files([
    "worker.py",
])
