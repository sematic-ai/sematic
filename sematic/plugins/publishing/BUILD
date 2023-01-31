sematic_py_lib(
    name = "slack",
    srcs = ["slack.py"],
    pip_deps = ["requests"],
    deps = [
        "//sematic:abstract_plugin",
        "//sematic/config:server_settings",
        "//sematic/config:settings",
        "//sematic/db:queries",
        "//sematic/db/models:resolution",
        "//sematic/plugins:abstract_publisher",
    ],
)
