sematic_py_lib(
    name = "fixtures",
    srcs = ["fixtures.py"],
    visibility = ["//visibility:public"],
    deps = [
        "//sematic/db/tests:fixtures",
        "//sematic/api:server_lib",
        requirement("pytest"),
        requirement("werkzeug"),
        requirement("responses"),
    ]
)

pytest_test(
    name = "test_server",
    srcs = ["test_server.py"],
    deps = [
        ":fixtures",
        "//sematic/db/tests:fixtures",
        requirement("flask")
    ]
)