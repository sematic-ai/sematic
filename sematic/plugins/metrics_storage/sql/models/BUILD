sematic_py_lib(
    name = "metric_label",
    srcs = ["metric_label.py"],
    pip_deps = ["sqlalchemy"],
    deps = [
        "//sematic/db/models:base",
        "//sematic/metrics:metric_point",
        "//sematic/utils:db",
    ],
)

sematic_py_lib(
    name = "metric_value",
    srcs = ["metric_value.py"],
    pip_deps = ["sqlalchemy"],
    deps = [
        ":metric_label",
        "//sematic/db/models:base",
    ],
)
