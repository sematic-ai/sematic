pytest_test(
    name = "test_calculator",
    srcs = ["test_calculator.py"],
    deps = [
        "//sematic:calculator",
        "//sematic:future",
        "//sematic/db/tests:fixtures",
    ],
)

pytest_test(
    name = "test_api_client",
    srcs = ["test_api_client.py"],
    deps = [
        "//sematic:api_client",
        "//sematic:config",
        "//sematic:versions",
    ],
)

pytest_test(
    name = "test_future",
    srcs = ["test_future.py"],
    deps = [
        "//sematic:calculator",
    ],
)

pytest_test(
    name = "test_init",
    srcs = ["test_init.py"],
    deps = [
        "//sematic:init",
    ],
)

pytest_test(
    name = "test_user_settings",
    srcs = ["test_user_settings.py"],
    deps = [
        "//sematic:config",
        "//sematic:user_settings",
    ],
)

sematic_py_lib(
    name = "fixtures",
    srcs = ["fixtures.py"],
    deps = [
        "//sematic:storage",
    ],
)
