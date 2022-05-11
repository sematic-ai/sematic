glow_py_lib(
    name = "base",
    srcs = ["base.py"],
    visibility = ["//visibility:public"],
    deps = [
        requirement("sqlalchemy"),
    ]
)

glow_py_lib(
    name = "json_encodable_mixin",
    srcs = ["json_encodable_mixin.py"],
    visibility = ["//visibility:public"],
    deps = [],
)

glow_py_lib(
    name = "run",
    srcs = ["run.py"],
    visibility = ["//visibility:public"],
    deps = [
        ":base",
        ":json_encodable_mixin",
        "//glow:abstract_future",
        requirement("sqlalchemy"),
    ]
)