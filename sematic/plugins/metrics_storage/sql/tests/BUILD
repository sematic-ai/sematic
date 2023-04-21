pytest_test(
    name = "test_sql_metrics_storage",
    srcs = ["test_sql_metrics_storage.py"],
    # buildifier: leave-alone
    deps = [
        "//sematic/db:db",
        "//sematic/db/tests:fixtures",
        "//sematic/metrics:metric_point",
        "//sematic/plugins:abstract_metrics_storage",
        "//sematic/plugins/metrics_storage/sql:sql_metrics_storage",
        "//sematic/plugins/metrics_storage/sql/models:metric_label",
        "//sematic/plugins/metrics_storage/sql/models:metric_value",
    ],
)
