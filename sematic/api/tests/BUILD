sematic_py_lib(
    name = "fixtures",
    srcs = ["fixtures.py"],
    pip_deps = [
        "pytest",
        "werkzeug",
        "responses",
    ],
    visibility = ["//visibility:public"],
    # buildifier: leave-alone
    deps = [
        "//sematic:abstract_plugin",
        "//sematic/api:server_lib",
        "//sematic/config:config",
        "//sematic/config:server_settings",
        "//sematic/config:settings",
        "//sematic/config:user_settings",
        "//sematic/db/tests:fixtures",
        "//sematic/plugins/storage:memory_storage",
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
