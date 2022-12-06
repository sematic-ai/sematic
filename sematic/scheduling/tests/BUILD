pytest_test(
    name = "test_job_scheduler",
    srcs = ["test_job_scheduler.py"],
    deps = [
        "//sematic:abstract_future",
        "//sematic/db/models:run",
        "//sematic/db/models:resolution",
        "//sematic/resolvers:resource_requirements",
        "//sematic/scheduling:job_scheduler",
        "//sematic/scheduling:kubernetes",
        "//sematic:versions",
    ],
)

pytest_test(
    name = "test_kubernetes",
    srcs = ["test_kubernetes.py"],
    deps = [
        "//sematic/config:server_settings",
        "//sematic/scheduling:kubernetes",
        "//sematic/resolvers:resource_requirements",
        "//sematic/tests:fixtures",
    ],
    pip_deps = [
        "kubernetes",
    ]
)
