glow_py_lib(
    name = "fixtures",
    srcs = ["fixtures.py"],
    visibility = ["//visibility:public"],
    deps = [
        "//glow/db/tests:fixtures",
        "//glow/api:server_lib",
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
        "//glow/db/tests:fixtures",
        requirement("flask")
    ]
)