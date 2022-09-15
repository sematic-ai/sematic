sematic_py_lib(
    name = "external_job",
    srcs = ["external_job.py"],
    deps = [
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
        "//sematic/utils:retry",
        "//sematic:config",
        "//sematic:container_images",
        "//sematic/scheduling:external_job",
        "//sematic/resolvers:resource_requirements"
    ],
    pip_deps = [
        "kubernetes",
    ],
)
