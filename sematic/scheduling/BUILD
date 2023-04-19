
sematic_py_lib(
    name = "job_details",
    srcs = ["job_details.py"],
    deps = [
        "//sematic/utils:exceptions",
    ],
)

sematic_py_lib(
    name = "job_scheduler",
    srcs = ["job_scheduler.py"],
    deps = [
        "//sematic:abstract_future",
        "//sematic/db/models:job",
        "//sematic/db/models:resolution",
        "//sematic/db/models:run",
        "//sematic/db:queries",
        "//sematic/scheduling:job_details",
        "//sematic/scheduling:kubernetes",
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
        "//sematic/db/models:factories",
        "//sematic/db/models:job",
        "//sematic/plugins/storage:s3_storage",
        "//sematic/resolvers:resource_requirements",
        "//sematic/scheduling:job_details",
        "//sematic/utils:exceptions",
        "//sematic/utils:retry",
    ],
    pip_deps = [
        "kubernetes",
    ],
)
