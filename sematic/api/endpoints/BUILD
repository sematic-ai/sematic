sematic_py_lib(
    name = "runs",
    srcs = ["runs.py"],
    deps = [
        "//sematic/api:app",
        "//sematic/db:db",
        "//sematic/db:queries",
        "//sematic/db/models:run",
        ":request_parameters",
        requirement("flask"),
        requirement("sqlalchemy"),
        requirement("flask-socketio")
    ]
)

sematic_py_lib(
    name = "artifacts",
    srcs = ["artifacts.py"],
    deps = [
        "//sematic/api:app",
        "//sematic/db:queries",
        requirement("flask"),
    ]
)

sematic_py_lib(
    name = "request_parameters",
    srcs = ["request_parameters.py"],
    deps = [
        requirement("sqlalchemy"),
        requirement("flask"),
    ]
)

sematic_py_lib(
    name = "edges",
    srcs = ["edges.py"],
    deps = [
        "//sematic/api:app",
        "//sematic/db:db",
        "//sematic/db/models:edge",
        ":request_parameters",
        requirement("flask"),
        requirement("sqlalchemy"),
    ]
)

sematic_py_lib(
    name = "notes",
    srcs = ["notes.py"],
    deps = [
        "//sematic/api:app",
        "//sematic/db:queries",
        "//sematic/db/models:note",
        ":request_parameters",
        requirement("flask"),
        requirement("sqlalchemy"),
    ]
)
