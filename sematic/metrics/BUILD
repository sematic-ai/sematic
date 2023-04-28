sematic_py_lib(
    name = "metric_point",
    srcs = ["metric_point.py"],
    deps = [],
)

sematic_py_lib(
    name = "run_count_metric",
    srcs = ["run_count_metric.py"],
    deps = [
        ":metric_point",
        "//sematic:abstract_system_metric",
        "//sematic/db/models:run",
    ],
)

sematic_py_lib(
    name = "func_success_rate_metric",
    srcs = ["func_success_rate_metric.py"],
    pip_deps = ["sqlalchemy"],
    deps = [
        "//sematic:abstract_future",
        "//sematic:abstract_system_metric",
        "//sematic/db/models:run",
        "//sematic/metrics:metric_point",
    ],
)
