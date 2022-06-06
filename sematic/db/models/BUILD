sematic_py_lib(
    name = "artifact",
    srcs = ["artifact.py"],
    deps = [
        ":base",
        ":json_encodable_mixin",
        requirement("sqlalchemy"),
    ]
)

sematic_py_lib(
    name = "base",
    srcs = ["base.py"],
    deps = [
        requirement("sqlalchemy"),
    ]
)

sematic_py_lib(
    name = "factories",
    srcs = ["factories.py"],
    deps = [
        ":artifact",
        ":run",
        "//sematic:abstract_future",
        "//sematic/types:serialization",
    ]
)

sematic_py_lib(
    name = "edge",
    srcs = ["edge.py"],
    deps = [
        ":base",
        ":json_encodable_mixin",
        requirement("sqlalchemy"),
    ]
)

sematic_py_lib(
    name = "json_encodable_mixin",
    srcs = ["json_encodable_mixin.py"],
    deps = [],
)

sematic_py_lib(
    name = "run",
    srcs = ["run.py"],
    deps = [
        ":base",
        ":json_encodable_mixin",
        "//sematic:abstract_future",
        requirement("sqlalchemy"),
    ]
)
