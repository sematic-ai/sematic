sematic_py_lib(
    name = "external_job",
    srcs = ["external_job.py"],
    deps = [
        "//sematic/utils:exceptions",
    ],
)

sematic_py_lib(
    name = "job_scheduler",
    srcs = ["job_scheduler.py"],
    deps = [
        "//sematic:abstract_future",
        "//sematic/db/models:resolution",
        "//sematic/db/models:run",
        "//sematic/scheduling:kubernetes",
        "//sematic/scheduling:external_job",
    ],
)

sematic_py_lib(
    name = "kubernetes",
    srcs = ["kubernetes.py"],
    deps = [
        "//sematic:container_images",
        "//sematic/config:config",
        "//sematic/config:user_settings",
        "//sematic/config:server_settings",
        "//sematic/config:settings",
        "//sematic/plugins/storage:s3_storage",
        "//sematic/resolvers:resource_requirements",
        "//sematic/scheduling:external_job",
        "//sematic/utils:exceptions",
        "//sematic/utils:retry",
    ],
    pip_deps = [
        "kubernetes",
    ],
)
