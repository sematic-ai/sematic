sematic_py_lib(
    name = "runs",
    srcs = ["runs.py"],
    pip_deps = [
        "flask",
        "sqlalchemy",
    ],
    # buildifier: leave-alone
    deps = [
        ":auth",
        ":metrics",
        ":payloads",
        ":request_parameters",
        "//sematic:log_reader",
        "//sematic/api:app",
        "//sematic/db:db",
        "//sematic/db:queries",
        "//sematic/db/models:artifact",
        "//sematic/db/models:edge",
        "//sematic/db/models:run",
        "//sematic/db/models:user",
        "//sematic/scheduling:job_scheduler",
        "//sematic/scheduling:kubernetes",
    ],
)

sematic_py_lib(
    name = "events",
    srcs = ["events.py"],
    pip_deps = [
        "flask",
        "flask-socketio",
        "requests",
    ],
    deps = [
        ":auth",
        "//sematic:api_client",
        "//sematic/api:app",
        "//sematic/db/models:user",
    ],
)

sematic_py_lib(
    name = "external_resources",
    srcs = ["external_resources.py"],
    pip_deps = [
        "flask",
    ],
    deps = [
        "//sematic/api:app",
        "//sematic/api/endpoints:auth",
        "//sematic/api/endpoints:request_parameters",
        "//sematic/db/models:external_resource",
        "//sematic/db/models:user",
        "//sematic/db:queries",

        # Included so there is always an ExternalResource implementation
        # the server can use for demonstrating the feature/API.
        "//sematic/plugins/external_resource:timed_message",
    ],
)

sematic_py_lib(
    name = "resolutions",
    srcs = ["resolutions.py"],
    pip_deps = [
        "flask",
        "sqlalchemy",
        "flask-socketio",
    ],
    deps = [
        ":auth",
        ":events",
        ":payloads",
        ":request_parameters",
        "//sematic/api:app",
        "//sematic/db:queries",
        "//sematic/db/models:resolution",
        "//sematic/db/models:user",
    ],
)

sematic_py_lib(
    name = "artifacts",
    srcs = ["artifacts.py"],
    pip_deps = [
        "flask",
    ],
    # buildifier: leave-alone
    deps = [
        ":auth",
        ":request_parameters",
        "//sematic/api:app",
        "//sematic/db:db",
        "//sematic/db:queries",
        "//sematic/db/models:artifact",
        "//sematic/db/models:user",
    ],
)

sematic_py_lib(
    name = "request_parameters",
    srcs = ["request_parameters.py"],
    pip_deps = [
        "sqlalchemy",
        "flask",
    ],
    deps = [],
)

sematic_py_lib(
    name = "edges",
    srcs = ["edges.py"],
    pip_deps = [
        "flask",
        "sqlalchemy",
    ],
    # buildifier: leave-alone
    deps = [
        ":request_parameters",
        "//sematic/api:app",
        "//sematic/db:db",
        "//sematic/db/models:edge",
    ],
)

sematic_py_lib(
    name = "meta",
    srcs = ["meta.py"],
    pip_deps = ["flask"],
    deps = [
        "//sematic:versions",
        "//sematic/api:app",
        "//sematic/config:server_settings",
        "//sematic/config:settings",
    ],
)

sematic_py_lib(
    name = "notes",
    srcs = ["notes.py"],
    pip_deps = [
        "flask",
        "sqlalchemy",
    ],
    # buildifier: leave-alone
    deps = [
        ":auth",
        ":payloads",
        ":request_parameters",
        "//sematic/api:app",
        "//sematic/db:db",
        "//sematic/db:queries",
        "//sematic/db/models:note",
        "//sematic/db/models:run",
        "//sematic/db/models:user",
    ],
)

sematic_py_lib(
    name = "auth",
    srcs = ["auth.py"],
    pip_deps = [
        "flask",
        "google-auth",
        "requests",
        "sqlalchemy",
    ],
    deps = [
        ":request_parameters",
        "//sematic/api:app",
        "//sematic/config:server_settings",
        "//sematic/config:settings",
        "//sematic/db:queries",
        "//sematic/db/models:factories",
    ],
)

sematic_py_lib(
    name = "storage",
    srcs = ["storage.py"],
    pip_deps = [
        "flask",
    ],
    deps = [
        ":auth",
        ":request_parameters",
        "//sematic/api:app",
        "//sematic/db/models:user",
        "//sematic/plugins:abstract_storage",
        "//sematic/plugins/storage:local_storage",
    ],
)

sematic_py_lib(
    name = "payloads",
    srcs = ["payloads.py"],
    deps = [
        "//sematic/db:queries",
        "//sematic/db/models:resolution",
        "//sematic/db/models:run",
    ],
)

sematic_py_lib(
    name = "metrics",
    srcs = ["metrics.py"],
    pip_deps = ["sqlalchemy"],
    deps = [
        "//sematic:abstract_system_metric",
        "//sematic/api:app",
        "//sematic/api/endpoints:auth",
        "//sematic/api/endpoints:request_parameters",
        "//sematic/db/models:run",
        "//sematic/db/models:user",
        "//sematic/metrics:func_success_rate_metric",
        "//sematic/metrics:metric_point",
        "//sematic/metrics:run_count_metric",
        "//sematic/plugins:abstract_metrics_storage",
        "//sematic/plugins/metrics_storage/sql:sql_metrics_storage",
    ],
)
