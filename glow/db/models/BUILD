glow_py_lib(
    name = "base",
    srcs = ["base.py"],
    deps = [
        requirement("sqlalchemy"),
    ]
)

glow_py_lib(
    name = "run",
    srcs = ["runs.py"],
    deps = [
        ":base",
        "//glow:abstract_future",
        requirement("sqlalchemy"),
    ]
)