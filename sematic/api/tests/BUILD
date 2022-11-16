sematic_py_lib(
    name = "fixtures",
    srcs = ["fixtures.py"],
    visibility = ["//visibility:public"],
    deps = [
        "//sematic/api:server_lib",
        "//sematic/config:user_settings",
        "//sematic/db/tests:fixtures",
        "//sematic/scheduling:kubernetes",
    ],
    pip_deps = [
        "pytest",
        "werkzeug",
        "responses",
    ],
)

pytest_test(
    name = "test_server",
    srcs = ["test_server.py"],
    deps = [
        ":fixtures",
        "//sematic/db/tests:fixtures",
    ],
    pip_deps = [
        "flask",
    ]
)
