sematic_py_lib(
    name = "artifact",
    srcs = ["artifact.py"],
    pip_deps = [
        "sqlalchemy",
    ],
    deps = [
        ":base",
        ":json_encodable_mixin",
    ],
)

sematic_py_lib(
    name = "base",
    srcs = ["base.py"],
    pip_deps = [
        "sqlalchemy",
    ],
    deps = [],
)

sematic_py_lib(
    name = "factories",
    srcs = ["factories.py"],
    deps = [
        ":artifact",
        ":run",
        ":user",
        "//sematic:abstract_future",
        "//sematic:storage",
        "//sematic/types:serialization",
    ],
)

sematic_py_lib(
    name = "edge",
    srcs = ["edge.py"],
    pip_deps = [
        "sqlalchemy",
    ],
    deps = [
        ":base",
        ":json_encodable_mixin",
    ],
)

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
    name = "run",
    srcs = ["run.py"],
    pip_deps = [
        "sqlalchemy",
    ],
    deps = [
        ":base",
        ":has_external_jobs_mixin",
        ":json_encodable_mixin",
        "//sematic:abstract_future",
        "//sematic/scheduling:external_job",
        "//sematic/types:serialization",
        "//sematic/utils:exceptions",
    ],
)

sematic_py_lib(
    name = "resolution",
    srcs = ["resolution.py"],
    pip_deps = [
        "sqlalchemy",
    ],
    deps = [
        ":base",
        ":has_external_jobs_mixin",
        ":json_encodable_mixin",
    ],
)

sematic_py_lib(
    name = "note",
    srcs = ["note.py"],
    pip_deps = [
        "sqlalchemy",
    ],
    deps = [
        ":base",
        ":json_encodable_mixin",
    ],
)

sematic_py_lib(
    name = "user",
    srcs = ["user.py"],
    pip_deps = [
        "sqlalchemy",
    ],
    deps = [
        ":base",
        ":json_encodable_mixin",
    ],
)
