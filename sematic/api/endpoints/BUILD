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
        "//sematic:log_reader",
        "//sematic/api:app",
        "//sematic/api/endpoints/utils:request_parameters",
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
    name = "external_resources",
    srcs = ["external_resources.py"],
    pip_deps = [
        "flask",
    ],
    deps = [
            "//sematic/api:app",
            "//sematic/api/endpoints:auth",
            "//sematic/api/endpoints/utils:request_parameters",
            "//sematic/db/models:external_resource",
            "//sematic/db/models:user",
            "//sematic/db:queries",

            # Included so there is always an ExternalResource implementation
            # the server can use for demonstrating the feature/API.
            "//sematic/plugins/external_resource:timed_message",
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
        "//sematic/api:app",
        "//sematic/api/endpoints/utils:request_parameters",
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
        "//sematic/api:app",
        "//sematic/api/endpoints/utils:request_parameters",
        "//sematic/api/endpoints/utils:storage",
        "//sematic/db:db",
        "//sematic/db:queries",
        "//sematic/db/models:artifact",
        "//sematic/db/models:user",
        "//sematic/plugins:abstract_storage",
    ],
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
        "//sematic/api:app",
        "//sematic/api/endpoints/utils:request_parameters",
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
        "//sematic/api:app",
        "//sematic/api/endpoints/utils:request_parameters",
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
        "//sematic/api:app",
        "//sematic/api/endpoints/utils:request_parameters",
        "//sematic/config:server_settings",
        "//sematic/config:settings",
        "//sematic/db:queries",
        "//sematic/db/models:factories",
    ],
)
