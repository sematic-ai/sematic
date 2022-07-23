sematic_py_lib(
    name = "runs",
    srcs = ["runs.py"],
    deps = [
        ":auth",
        ":request_parameters",
        "//sematic/api:app",
        "//sematic/db",
        "//sematic/db:queries",
        "//sematic/db/models:artifact",
        "//sematic/db/models:edge",
        "//sematic/db/models:run",
        "//sematic/db/models:user",
        requirement("flask"),
        requirement("sqlalchemy"),
        requirement("flask-socketio"),
    ],
)

sematic_py_lib(
    name = "artifacts",
    srcs = ["artifacts.py"],
    deps = [
        "//sematic/api:app",
        "//sematic/db:queries",
        requirement("flask"),
    ],
)

sematic_py_lib(
    name = "request_parameters",
    srcs = ["request_parameters.py"],
    deps = [
        requirement("sqlalchemy"),
        requirement("flask"),
    ],
)

sematic_py_lib(
    name = "edges",
    srcs = ["edges.py"],
    deps = [
        ":request_parameters",
        "//sematic/api:app",
        "//sematic/db",
        "//sematic/db/models:edge",
        requirement("flask"),
        requirement("sqlalchemy"),
    ],
)

sematic_py_lib(
    name = "notes",
    srcs = ["notes.py"],
    deps = [
        ":auth",
        ":request_parameters",
        "//sematic/api:app",
        "//sematic/db",
        "//sematic/db:queries",
        "//sematic/db/models:note",
        "//sematic/db/models:run",
        "//sematic/db/models:user",
        requirement("flask"),
        requirement("sqlalchemy"),
    ],
)

sematic_py_lib(
    name = "auth",
    srcs = ["auth.py"],
    deps = [
        ":request_parameters",
        "//sematic:config",
        "//sematic/api:app",
        "//sematic/db:queries",
        "//sematic/db/models:factories",
        requirement("flask"),
        requirement("google-auth"),
        requirement("requests"),
        requirement("sqlalchemy"),
    ],
)
