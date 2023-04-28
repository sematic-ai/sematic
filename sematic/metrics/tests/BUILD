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

pytest_test(
    name = "test_func_success_rate_metric",
    srcs = ["test_func_success_rate_metric.py"],
    # buildifier: leave-alone
    deps = [
        "//sematic:abstract_future",
        "//sematic/db:db",
        "//sematic/db/models:run",
        "//sematic/db/tests:fixtures",
        "//sematic/metrics:func_success_rate_metric",
        "//sematic/metrics:metric_point",
        "//sematic/plugins:abstract_metrics_storage",
        "//sematic/plugins/metrics_storage/sql:sql_metrics_storage",
        "//sematic/plugins/metrics_storage/sql/models:metric_value",
    ],
)

sematic_py_lib(
    name = "fixtures",
    srcs = ["fixtures.py"],
    pip_deps = ["pytest"],
    # buildifier: leave-alone
    deps = [
        "//sematic/db:db",
        "//sematic/db/tests:fixtures",
        "//sematic/metrics:metric_point",
        "//sematic/plugins/metrics_storage/sql:sql_metrics_storage",
    ],
)
