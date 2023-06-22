
sematic_py_lib(
    name = "check",
    srcs = ["check.py"],
    pip_deps = [
        "requests",
    ],
    deps = [
        "//sematic:abstract_future",
        "//sematic:abstract_plugin",
        "//sematic/config:server_settings",
        "//sematic/config:settings",
        "//sematic/db:db",
        "//sematic/db/models/mixins:json_encodable_mixin",
        "//sematic/db/models:git_info",
        "//sematic/db/models:resolution",
        "//sematic/db/models:run",
    ],
)

sematic_py_lib(
    name = "endpoints",
    srcs = ["endpoints.py"],
    pip_deps = [
        "flask",
    ],
    deps = [
        ":check",
        "//sematic/api:app",
        "//sematic/api/endpoints:auth",
        "//sematic/db/models:organization",
        "//sematic/db/models:user",
    ],
)

sematic_py_lib(
    name = "publisher",
    srcs = ["publisher.py"],
    pip_deps = [],
    deps = [
        ":check",
        "//sematic/ee/plugins/publishing/github:endpoints", 
        "//sematic:abstract_plugin",
        "//sematic/config:server_settings",
        "//sematic/config:settings",
        "//sematic/db/models:resolution",
        "//sematic/db:queries",
        "//sematic/plugins:abstract_publisher",
    ],
)


