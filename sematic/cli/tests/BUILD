pytest_test(
    name = "test_main",
    srcs = ["test_main.py"],
    pip_deps = [
        "click",
    ],
    deps = [
        "//sematic:config",
        "//sematic/cli:main_lib",
        "//sematic/cli:process_utils",
        "//sematic/db/tests:fixtures",
    ],
)

pytest_test(
    name = "test_new",
    srcs = ["test_new.py"],
    pip_deps = [
        "click",
    ],
    deps = [
        "//sematic/cli:examples_utils",
        "//sematic/cli:new",
    ],
)

pytest_test(
    name = "test_cancel",
    srcs = ["test_cancel.py"],
    pip_deps = [
        "click",
    ],
    deps = [
        "//sematic/cli:cancel",
        "//sematic/db/models:run",
        "//sematic/db/tests:fixtures",
    ],
)
