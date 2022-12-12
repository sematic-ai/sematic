sematic_py_lib(
    name = "google_auth",
    srcs = ["google_auth.py"],
    pip_deps = [
        "flask",
        "google-auth",
        "sqlalchemy",
    ],
    deps = [
        "//sematic:abstract_plugin",
        "//sematic/api:app",
        "//sematic/api/endpoints:request_parameters",
        "//sematic/config:server_settings",
        "//sematic/config:settings",
        "//sematic/db:queries",
        "//sematic/db/models:factories",
        "//sematic/plugins:abstract_auth",
    ],
)
