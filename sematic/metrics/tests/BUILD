pytest_test(
    name = "test_metric_point",
    srcs = ["test_metric_point.py"],
    deps = [
        "//sematic/metrics:metric_point",
    ],
)

pytest_test(
    name = "test_run_count_metric",
    srcs = ["test_run_count_metric.py"],
    # buildifier: leave-alone
    deps = [
        "//sematic:abstract_future",
        "//sematic/db:db",
        "//sematic/db/models:run",
        "//sematic/db/tests:fixtures",
        "//sematic/metrics:run_count_metric",
        "//sematic/metrics:metric_point",
        "//sematic/plugins/metrics_storage/sql/models:metric_value",
        "//sematic/plugins/metrics_storage/sql:sql_metrics_storage",
        "//sematic/plugins:abstract_metrics_storage",
    ],
)
