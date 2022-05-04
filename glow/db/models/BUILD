glow_py_lib(
    name = "base",
    srcs = ["base.py"],
    visibility = ["//visibility:public"],
    deps = [
        requirement("sqlalchemy"),
    ]
)

glow_py_lib(
    name = "run",
    srcs = ["run.py"],
    visibility = ["//visibility:public"],
    deps = [
        ":base",
        "//glow:abstract_future",
        requirement("sqlalchemy"),
    ]
)