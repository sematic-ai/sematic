pytest_test(
    name = "test_config_dir",
    srcs = ["test_config_dir.py"],
    deps = [
        "//sematic/config:config_dir",
        "//sematic/tests:fixtures",
    ],
)

pytest_test(
    name = "test_user_settings",
    srcs = ["test_user_settings.py"],
    deps = [
        # buildifier: leave-alone
        "//sematic/config:config",
        "//sematic/config:user_settings",
    ],
)

pytest_test(
    name = "test_server_settings",
    srcs = ["test_server_settings.py"],
    deps = [
        "//sematic/config:server_settings",
    ],
)
