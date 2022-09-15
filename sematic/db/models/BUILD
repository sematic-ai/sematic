sematic_py_lib(
    name = "artifact",
    srcs = ["artifact.py"],
    deps = [
        ":base",
        ":json_encodable_mixin",
    ],
    pip_deps = [
        "sqlalchemy"
    ],
)

sematic_py_lib(
    name = "base",
    srcs = ["base.py"],
    deps = [],
    pip_deps = [
        "sqlalchemy"
    ],
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
    deps = [
        ":base",
        ":json_encodable_mixin",
    ],
    pip_deps = [
        "sqlalchemy",
    ],
)

sematic_py_lib(
    name = "json_encodable_mixin",
    srcs = ["json_encodable_mixin.py"],
    deps = [],
    pip_deps = [
        "python-dateutil",
        "sqlalchemy",
    ],
)

sematic_py_lib(
    name = "run",
    srcs = ["run.py"],
    deps = [
        ":base",
        ":json_encodable_mixin",
        "//sematic:abstract_future",
        "//sematic/scheduling:external_job",
        "//sematic/types:serialization",
    ],
    pip_deps = [
        "sqlalchemy",
    ],
)

sematic_py_lib(
    name = "resolution",
    srcs = ["resolution.py"],
    deps = [
        ":base",
        ":json_encodable_mixin",
    ],
    pip_deps = [
        "sqlalchemy",
    ],
)

sematic_py_lib(
    name = "note",
    srcs = ["note.py"],
    deps = [
        ":base",
        ":json_encodable_mixin",
    ],
    pip_deps = [
        "sqlalchemy",
    ],
)

sematic_py_lib(
    name = "user",
    srcs = ["user.py"],
    deps = [
        ":base",
        ":json_encodable_mixin",
    ],
    pip_deps = [
        "sqlalchemy",
    ],
)
