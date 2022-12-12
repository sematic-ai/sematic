sematic_py_lib(
    name = "memory_storage",
    srcs = ["memory_storage.py"],
    deps = [
        "//sematic:abstract_plugin",
        "//sematic/plugins:abstract_storage",
    ],
)

sematic_py_lib(
    name = "local_storage",
    srcs = ["local_storage.py"],
    # buildifier: leave-alone
    deps = [
        "//sematic/plugins:abstract_storage",
        "//sematic:abstract_plugin",
        "//sematic/config:config",
    ],
)

sematic_py_lib(
    name = "s3_storage",
    srcs = ["s3_storage.py"],
    pip_deps = [
        "boto3",
        "requests",
    ],
    deps = [
        "//sematic:abstract_plugin",
        "//sematic/config:user_settings",
        "//sematic/plugins:abstract_storage",
        "//sematic/utils:memoized_property",
        "//sematic/utils:retry",
    ],
)
