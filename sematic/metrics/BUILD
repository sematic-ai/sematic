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
