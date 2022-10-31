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
        "//sematic:config",
        "//sematic:container_images",
        "//sematic/scheduling:external_job",
        "//sematic/resolvers:resource_requirements",
        "//sematic/utils:exceptions",
        "//sematic/utils:retry",
    ],
    pip_deps = [
        "kubernetes",
    ],
)
