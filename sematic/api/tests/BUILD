sematic_py_lib(
    name = "fixtures",
    srcs = ["fixtures.py"],
    visibility = ["//visibility:public"],
    deps = [
        "//sematic:user_settings",
        "//sematic/api:server_lib",
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
