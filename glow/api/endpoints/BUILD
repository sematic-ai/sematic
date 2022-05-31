glow_py_lib(
    name = "runs",
    srcs = ["runs.py"],
    deps = [
        "//glow/api:app",
        "//glow/db:db",
        "//glow/db:queries",
        "//glow/db/models:run",
        ":request_parameters",
        requirement("flask"),
        requirement("sqlalchemy"),
        requirement("flask-socketio")
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

glow_py_lib(
    name = "request_parameters",
    srcs = ["request_parameters.py"],
    deps = [
        requirement("sqlalchemy"),
    ]
)

glow_py_lib(
    name = "edges",
    srcs = ["edges.py"],
    deps = [
        "//glow/api:app",
        "//glow/db:db",
        "//glow/db/models:edge",
        ":request_parameters",
        requirement("flask"),
        requirement("sqlalchemy"),
    ]
)
