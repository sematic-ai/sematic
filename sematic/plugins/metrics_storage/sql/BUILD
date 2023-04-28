sematic_py_lib(
    name = "sql_metrics_storage",
    srcs = ["sql_metrics_storage.py"],
    pip_deps = ["sqlalchemy"],
    # buildifier: leave-alone
    deps = [
        "//sematic:abstract_plugin",
        "//sematic/config:config",
        "//sematic/db:db",
        "//sematic/metrics:metric_point",
        "//sematic/plugins:abstract_metrics_storage",
        "//sematic/plugins/metrics_storage/sql/models:metric_label",
        "//sematic/plugins/metrics_storage/sql/models:metric_value",
        "//sematic/utils:hashing",
    ],
)
