sematic_py_lib(
    name = "runs",
    srcs = ["runs.py"],
    deps = [
        ":auth",
        ":request_parameters",
        "//sematic/api:app",
        "//sematic/db:db",
        "//sematic/db:queries",
        "//sematic/db/models:artifact",
        "//sematic/db/models:edge",
        "//sematic/db/models:run",
        "//sematic/db/models:user",
        "//sematic:log_reader",
        "//sematic/scheduling:job_scheduler",
    ],
    pip_deps = [
        "flask",
        "sqlalchemy",
        "flask-socketio",
    ],
)

sematic_py_lib(
    name = "resolutions",
    srcs = ["resolutions.py"],
    deps = [
        ":auth",
        ":request_parameters",
        "//sematic/api:app",
        "//sematic/db:queries",
        "//sematic/db/models:resolution",
        "//sematic/db/models:user",
    ],
    pip_deps = [
        "flask",
        "sqlalchemy",
    ],
)

sematic_py_lib(
    name = "artifacts",
    srcs = ["artifacts.py"],
    deps = [
        "//sematic/api:app",
        "//sematic/db:queries",
    ],
    pip_deps = [
        "flask",
    ],
)

sematic_py_lib(
    name = "request_parameters",
    srcs = ["request_parameters.py"],
    deps = [],
    pip_deps = [
        "sqlalchemy",
        "flask",
    ]
)

sematic_py_lib(
    name = "edges",
    srcs = ["edges.py"],
    deps = [
        ":request_parameters",
        "//sematic/api:app",
        "//sematic/db:db",
        "//sematic/db/models:edge",
    ],
    pip_deps = [
        "flask",
        "sqlalchemy",
    ]
)

sematic_py_lib(
    name = "meta",
    srcs = ["meta.py"],
    deps = [
        "//sematic/api:app",
        "//sematic:versions",
    ],
    pip_deps = ["flask"]
)

sematic_py_lib(
    name = "notes",
    srcs = ["notes.py"],
    deps = [
        ":auth",
        ":request_parameters",
        "//sematic/api:app",
        "//sematic/db:db",
        "//sematic/db:queries",
        "//sematic/db/models:note",
        "//sematic/db/models:run",
        "//sematic/db/models:user",
    ],
    pip_deps = [
        "flask",
        "sqlalchemy",
    ]
)

sematic_py_lib(
    name = "auth",
    srcs = ["auth.py"],
    deps = [
        ":request_parameters",
        "//sematic:user_settings",
        "//sematic/api:app",
        "//sematic/db:queries",
        "//sematic/db/models:factories",
    ],
    pip_deps = [
        "flask",
        "google-auth",
        "requests",
        "sqlalchemy",
    ]
)
