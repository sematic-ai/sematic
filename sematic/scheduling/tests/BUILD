pytest_test(
    name = "test_job_scheduler",
    srcs = ["test_job_scheduler.py"],
    deps = [
        "//sematic:abstract_future",
        "//sematic:versions",
        "//sematic/db/models:resolution",
        "//sematic/db/models:run",
        "//sematic/db/models:job",
        "//sematic/db/tests:fixtures",
        "//sematic/resolvers:resource_requirements",
        "//sematic/scheduling:job_scheduler",
        "//sematic/scheduling:kubernetes",
    ],
)

pytest_test(
    name = "test_kubernetes",
    srcs = ["test_kubernetes.py"],
    pip_deps = [
        "kubernetes",
    ],
    deps = [
        "//sematic/api/tests:fixtures",
        "//sematic/config:server_settings",
        "//sematic/db/tests:fixtures",
        "//sematic/resolvers:resource_requirements",
        "//sematic/scheduling:kubernetes",
        "//sematic/tests:fixtures",
    ],
)
