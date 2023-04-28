pytest_test(
    name = "test_external_resources",
    srcs = ["test_external_resources.py"],
    pip_deps = [
        "flask",
    ],
    deps = [
        "//sematic/api/tests:fixtures",
        "//sematic/db/models:external_resource",
        "//sematic/db/models:user",
        "//sematic/db/tests:fixtures",
        "//sematic/plugins:abstract_external_resource",
    ],
)

pytest_test(
    name = "test_resolutions",
    srcs = ["test_resolutions.py"],
    pip_deps = [
        "flask",
    ],
    deps = [
        "//sematic:abstract_future",
        "//sematic:abstract_plugin",
        "//sematic/api/tests:fixtures",
        "//sematic/db:queries",
        "//sematic/db/models:resolution",
        "//sematic/db/models:run",
        "//sematic/db/models:user",
        "//sematic/db/tests:fixtures",
        "//sematic/plugins:abstract_publisher",
        "//sematic/scheduling:kubernetes",
        "//sematic/tests:fixtures",
    ],
)

pytest_test(
    name = "test_runs",
    srcs = ["test_runs.py"],
    pip_deps = [
        "flask",
    ],
    deps = [
        "//sematic:abstract_future",
        "//sematic:api_client",
        "//sematic:calculator",
        "//sematic:log_reader",
        "//sematic/api/tests:fixtures",
        "//sematic/config:server_settings",
        "//sematic/config:user_settings",
        "//sematic/config/tests:fixtures",
        "//sematic/db:queries",
        "//sematic/db/models:job",
        "//sematic/db/models:resolution",
        "//sematic/db/models:run",
        "//sematic/db/models:user",
        "//sematic/db/tests:fixtures",
        "//sematic/metrics:run_count_metric",
        "//sematic/scheduling:job_details",
        "//sematic/scheduling:kubernetes",
        "//sematic/tests:fixtures",
        "//sematic/utils:exceptions",
    ],
)

pytest_test(
    name = "test_notes",
    srcs = ["test_notes.py"],
    pip_deps = [
        "flask",
        "sqlalchemy",
    ],
    deps = [
        "//sematic/api/tests:fixtures",
        "//sematic/db:queries",
        "//sematic/db/models:note",
        "//sematic/db/models:run",
        "//sematic/db/models:user",
        "//sematic/db/tests:fixtures",
    ],
)

pytest_test(
    name = "test_auth",
    srcs = ["test_auth.py"],
    pip_deps = [
        "flask",
    ],
    deps = [
        "//sematic/api/endpoints:auth",
        "//sematic/api/tests:fixtures",
        "//sematic/config:server_settings",
        "//sematic/config:settings",
        "//sematic/db:queries",
        "//sematic/db/models:user",
        "//sematic/db/models/mixins:json_encodable_mixin",
    ],
)

pytest_test(
    name = "test_meta",
    srcs = ["test_meta.py"],
    pip_deps = [
        "flask",
    ],
    deps = [
        "//sematic:versions",
        "//sematic/api:app",
        "//sematic/api/endpoints:meta",
        "//sematic/api/tests:fixtures",
        "//sematic/config:server_settings",
    ],
)

pytest_test(
    name = "test_artifacts",
    srcs = ["test_artifacts.py"],
    pip_deps = [
        "flask",
    ],
    deps = [
        "//sematic/api/tests:fixtures",
        "//sematic/db/models:artifact",
        "//sematic/db/tests:fixtures",
        "//sematic/tests:fixtures",
    ],
)

pytest_test(
    name = "test_storage",
    srcs = ["test_storage.py"],
    pip_deps = [
        "flask",
    ],
    deps = [
        "//sematic/api/tests:fixtures",
        "//sematic/db/tests:fixtures",
    ],
)

pytest_test(
    name = "test_metrics",
    srcs = ["test_metrics.py"],
    deps = [
        "//sematic:abstract_future",
        "//sematic/api/endpoints:metrics",
        "//sematic/api/tests:fixtures",
        "//sematic/db/models:run",
        "//sematic/db/tests:fixtures",
        "//sematic/metrics:func_success_rate_metric",
        "//sematic/metrics:metric_point",
        "//sematic/metrics:run_count_metric",
        "//sematic/metrics/tests:fixtures",
        "//sematic/plugins:abstract_metrics_storage",
        "//sematic/plugins/metrics_storage/sql:sql_metrics_storage",
    ],
)
