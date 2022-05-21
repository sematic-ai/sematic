glow_py_lib(
    name = "runs",
    srcs = ["runs.py"],
    deps = [
        "//glow/api:app",
        "//glow/db:db",
        "//glow/db:queries",
        "//glow/db/models:run",
        requirement("flask"),
        requirement("sqlalchemy"),
    ]
)

glow_py_lib(
    name = "artifacts",
    srcs = ["artifacts.py"],
    deps = [
        "//glow/api:app",
        "//glow/db:queries",
        requirement("flask"),
    ]
)