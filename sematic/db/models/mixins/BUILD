sematic_py_lib(
    name = "has_external_jobs_mixin",
    srcs = ["has_external_jobs_mixin.py"],
    deps = [
        "//sematic/scheduling:external_job",
        "//sematic/types:serialization",
        "//sematic/types/types:dataclass",
    ],
)

sematic_py_lib(
    name = "json_encodable_mixin",
    srcs = ["json_encodable_mixin.py"],
    pip_deps = [
        "python-dateutil",
        "sqlalchemy",
    ],
    deps = [],
)

sematic_py_lib(
    name = "has_user_mixin",
    srcs = ["has_user_mixin.py"],
    pip_deps = [
        "sqlalchemy",
    ],
    deps = [],
)
