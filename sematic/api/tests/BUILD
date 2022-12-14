sematic_py_lib(
    name = "fixtures",
    srcs = ["fixtures.py"],
    pip_deps = [
        "pytest",
        "werkzeug",
        "responses",
    ],
    visibility = ["//visibility:public"],
    deps = [
        "//sematic/api:server_lib",
        "//sematic/config:server_settings",
        "//sematic/config:settings",
        "//sematic/config:user_settings",
        "//sematic/db/tests:fixtures",
        "//sematic/scheduling:kubernetes",
    ],
)

pytest_test(
    name = "test_server",
    srcs = ["test_server.py"],
    pip_deps = [
        "flask",
    ],
    deps = [
        ":fixtures",
        "//sematic/db/tests:fixtures",
    ],
)
