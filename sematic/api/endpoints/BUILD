sematic_py_lib(
    name = "runs",
    srcs = ["runs.py"],
    pip_deps = [
        "flask",
        "sqlalchemy",
    ],
    # buildifier: leave-alone
    deps = [
        ":auth",
        ":request_parameters",
        ":storage",
        "//sematic:log_reader",
        "//sematic/api:app",
        "//sematic/db:db",
        "//sematic/db:queries",
        "//sematic/db/models:artifact",
        "//sematic/db/models:edge",
        "//sematic/db/models:run",
        "//sematic/db/models:user",
        "//sematic/scheduling:job_scheduler",
    ],
)

sematic_py_lib(
    name = "events",
    srcs = ["events.py"],
    pip_deps = [
        "flask",
        "flask-socketio",
    ],
    deps = [
        ":auth",
        "//sematic/api:app",
        "//sematic/db/models:user",
    ],
)

sematic_py_lib(
    name = "resolutions",
    srcs = ["resolutions.py"],
    pip_deps = [
        "flask",
        "sqlalchemy",
        "flask-socketio",
    ],
    deps = [
        ":auth",
        ":events",
        ":request_parameters",
        "//sematic/api:app",
        "//sematic/db:queries",
        "//sematic/db/models:resolution",
        "//sematic/db/models:user",
    ],
)

sematic_py_lib(
    name = "artifacts",
    srcs = ["artifacts.py"],
    pip_deps = [
        "flask",
    ],
    # buildifier: leave-alone
    deps = [
        ":auth",
        ":request_parameters",
        ":storage",
        "//sematic/api:app",
        "//sematic/db:db",
        "//sematic/db:queries",
        "//sematic/db/models:artifact",
        "//sematic/db/models:user",
    ],
)

sematic_py_lib(
    name = "request_parameters",
    srcs = ["request_parameters.py"],
    pip_deps = [
        "sqlalchemy",
        "flask",
    ],
    deps = [],
)

sematic_py_lib(
    name = "edges",
    srcs = ["edges.py"],
    pip_deps = [
        "flask",
        "sqlalchemy",
    ],
    # buildifier: leave-alone
    deps = [
        ":request_parameters",
        "//sematic/api:app",
        "//sematic/db:db",
        "//sematic/db/models:edge",
    ],
)

sematic_py_lib(
    name = "meta",
    srcs = ["meta.py"],
    pip_deps = ["flask"],
    deps = [
        "//sematic:versions",
        "//sematic/api:app",
        "//sematic/config:server_settings",
        "//sematic/config:settings",
    ],
)

sematic_py_lib(
    name = "notes",
    srcs = ["notes.py"],
    pip_deps = [
        "flask",
        "sqlalchemy",
    ],
    # buildifier: leave-alone
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
)

sematic_py_lib(
    name = "auth",
    srcs = ["auth.py"],
    pip_deps = [
        "flask",
        "google-auth",
        "requests",
        "sqlalchemy",
    ],
    deps = [
        ":request_parameters",
        "//sematic/api:app",
        "//sematic/config:server_settings",
        "//sematic/config:settings",
        "//sematic/db:queries",
        "//sematic/db/models:factories",
    ],
)

sematic_py_lib(
    name = "storage",
    srcs = ["storage.py"],
    deps = [
        "//sematic:storage",
        "//sematic/config:user_settings",
    ],
)
