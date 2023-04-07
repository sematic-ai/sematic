sematic_py_lib(
    name = "func_success_rate",
    srcs = ["func_success_rate.py"],
    pip_deps = ["sqlalchemy"],
    deps = [
        ":types",
        "//sematic:abstract_future",
        "//sematic:abstract_metric",
        "//sematic/db/models:run",
    ],
)

sematic_py_lib(
    name = "func_effective_runtime",
    srcs = ["func_effective_runtime.py"],
    pip_deps = ["sqlalchemy"],
    deps = [
        ":types",
        "//sematic:abstract_future",
        "//sematic:abstract_metric",
        "//sematic/db/models:run",
    ],
)

sematic_py_lib(
    name = "func_run_count",
    srcs = ["func_run_count.py"],
    pip_deps = ["sqlalchemy"],
    deps = [
        ":types",
        "//sematic:abstract_metric",
        "//sematic/db/models:run",
    ],
)

sematic_py_lib(
    name = "cli_lib",
    srcs = ["cli.py"],
    pip_deps = ["click"],
    # buildifier: leave-alone
    deps = [
        ":func_effective_runtime",
        ":func_run_count",
        ":func_success_rate",
        "//sematic:abstract_metric",
        "//sematic/config:config",
        "//sematic/metrics:types",
    ],
)

py_binary(
    name = "metrics",
    srcs = ["cli.py"],
    main = "cli.py",
    deps = [":cli_lib"],
)

sematic_py_lib(
    name = "types",
    srcs = ["types_.py"],
    deps = [],
)

sematic_py_lib(
    name = "metrics_lib",
    srcs = ["metrics.py"],
    deps = [
        ":func_effective_runtime",
        ":func_run_count",
        ":func_success_rate",
        ":types",
        "//sematic:abstract_metric",
        "//sematic/db/models:run",
        "//sematic/plugins:abstract_metrics_storage",
        "//sematic/plugins/metrics_storage/pg:pg_metrics_storage",
    ],
)
