pytest_test(
    name = "test_config",
    srcs = ["test_config.py"],
    deps = [
        "//sematic/config:config",
    ],
)

pytest_test(
    name = "test_config_dir",
    srcs = ["test_config_dir.py"],
    deps = [
        "//sematic/config:config_dir",
        "//sematic/utils:env",
    ],
)

pytest_test(
    name = "test_user_settings",
    srcs = ["test_user_settings.py"],
    # buildifier: leave-alone
    deps = [
        ":fixtures",
        "//sematic/config:user_settings",
    ],
)

pytest_test(
    name = "test_server_settings",
    srcs = ["test_server_settings.py"],
    deps = [
        ":fixtures",
        "//sematic/config:server_settings",
    ],
)

pytest_test(
    name = "test_settings",
    srcs = ["test_settings.py"],
    deps = [
        ":fixtures",
        "//sematic:abstract_plugin",
        "//sematic/config:settings",
        "//sematic/plugins/storage:local_storage",
        "//sematic/utils:env",
    ],
)

sematic_py_lib(
    name = "fixtures",
    srcs = ["fixtures.py"],
    pip_deps = [
        "pyyaml",
        "pytest",
    ],
    deps = [
        "//sematic/config:server_settings",
        "//sematic/config:settings",
        "//sematic/config:user_settings",
    ],
)
