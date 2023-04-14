sematic_py_lib(
    name = "metric_point",
    srcs = ["metric_point.py"],
    deps = [],
)

sematic_py_lib(
    name = "func_run_count",
    srcs = ["func_run_count.py"],
    deps = [
        ":metric_point",
        "//sematic:abstract_metric",
        "//sematic/db/models:run",
    ],
)
