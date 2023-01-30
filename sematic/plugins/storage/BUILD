sematic_py_lib(
    name = "local_storage",
    srcs = ["local_storage.py"],
    pip_deps = ["flask"],
    # buildifier: leave-alone
    deps = [
        "//sematic:abstract_plugin",
        "//sematic/api:app",
        "//sematic/api/endpoints:auth",
        "//sematic/api/endpoints:request_parameters",
        "//sematic/config:config",
        "//sematic/config:server_settings",
        "//sematic/db/models:user",
        "//sematic/plugins:abstract_storage",
    ],
)

sematic_py_lib(
    name = "memory_storage",
    srcs = ["memory_storage.py"],
    pip_deps = ["flask"],
    deps = [
        "//sematic:abstract_plugin",
        "//sematic/api:app",
        "//sematic/api/endpoints:auth",
        "//sematic/api/endpoints:request_parameters",
        "//sematic/db/models:user",
        "//sematic/plugins:abstract_storage",
    ],
)

sematic_py_lib(
    name = "s3_storage",
    srcs = ["s3_storage.py"],
    pip_deps = [
        "boto3",
    ],
    deps = [
        "//sematic:abstract_plugin",
        "//sematic/config:settings",
        "//sematic/plugins:abstract_storage",
        "//sematic/utils:memoized_property",
        "//sematic/utils:retry",
    ],
)
