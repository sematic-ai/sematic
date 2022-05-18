glow_py_lib(
    name = "artifact",
    srcs = ["artifact.py"],
    deps = [
        ":base",
        ":json_encodable_mixin",
        requirement("sqlalchemy"),
    ]
)

glow_py_lib(
    name = "base",
    srcs = ["base.py"],
    deps = [
        requirement("sqlalchemy"),
    ]
)

glow_py_lib(
    name = "factories",
    srcs = ["factories.py"],
    deps = [
        ":artifact",
        ":run",
        "//glow:abstract_future",
        "//glow/types:serialization",
    ]
)

glow_py_lib(
    name = "json_encodable_mixin",
    srcs = ["json_encodable_mixin.py"],
    deps = [],
)

glow_py_lib(
    name = "run",
    srcs = ["run.py"],
    deps = [
        ":base",
        ":json_encodable_mixin",
        "//glow:abstract_future",
        requirement("sqlalchemy"),
    ]
)

glow_py_lib(
    name = "run_artifact",
    srcs = ["run_artifact.py"],
    deps = [
        ":base",
        requirement("sqlalchemy"),
    ]
)
