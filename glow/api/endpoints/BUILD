glow_py_lib(
    name = "runs",
    srcs = ["runs.py"],
    visibility = ["//visibility:public"],
    deps = [
        "//glow/api:app",
        "//glow/db:db",
        "//glow/db:queries",
        "//glow/db/models:run",
        requirement("flask"),
        requirement("sqlalchemy"),
    ]
)