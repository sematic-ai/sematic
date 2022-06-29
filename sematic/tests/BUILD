pytest_test(
    name = "test_calculator",
    srcs = ["test_calculator.py"],
    deps = [
        "//sematic:calculator",
        "//sematic:future",
        "//sematic/db/tests:fixtures",
        "//sematic/api/tests:fixtures",
    ]
)

pytest_test(
    name = "test_future",
    srcs = ["test_future.py"],
    deps = [
        "//sematic:calculator"
    ]
)

pytest_test(
    name = "test_init",
    srcs = ["test_init.py"],
    deps = [
        "//sematic:init",
    ]
)

pytest_test(
    name = "test_credentials",
    srcs = ["test_credentials.py"],
    deps = [
        "//sematic:credentials",
        "//sematic:config",
    ]
)