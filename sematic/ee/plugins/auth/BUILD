sematic_py_lib(
    name = "auth0_auth",
    srcs = ["auth0_auth.py"],
    pip_deps = [
        "flask",
        "auth0",
    ],
    deps = [
        "//sematic:abstract_plugin",
        "//sematic/api:app",
        "//sematic/api/endpoints:request_parameters",
        "//sematic/config:settings",
        "//sematic/plugins:abstract_auth",
    ],
)
