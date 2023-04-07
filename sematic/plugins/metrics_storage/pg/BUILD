sematic_py_lib(
    name = "pg_metrics_storage",
    srcs = ["pg_metrics_storage.py"],
    pip_deps = [
        "sqlalchemy",
    ],
    # buildifier: leave-alone
    deps = [
        "//sematic:abstract_plugin",
        "//sematic/db:db",
        "//sematic/plugins:abstract_metrics_storage",
        "//sematic/plugins/metrics_storage/pg/db/models:metric_label",
        "//sematic/plugins/metrics_storage/pg/db/models:metric_value",
        "//sematic/metrics:types",
        "//sematic/utils:hashing",
    ],
)
