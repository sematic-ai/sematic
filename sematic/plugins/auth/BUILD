sematic_py_lib(
    name = "google_auth",
    srcs = ["google_auth.py"],
    pip_deps = [
        "flask",
        "google-auth",
        "sqlalchemy",
    ],
    deps = [
        "/sematic/api:app",
        "//sematic/api/endpoints:request_parameters",
        "//sematic/config:settings",
        "//sematic/plugins:abstract_auth",
    ],
)
