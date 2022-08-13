pytest_test(
    name = "test_main",
    srcs = ["test_main.py"],
    deps = [
        "//sematic/cli:main_lib",
        "//sematic/cli:process_utils",
        "//sematic:config",
        "//sematic/db/tests:fixtures",
    ],
    pip_deps = [
        "click",
    ],
)

pytest_test(
    name = "test_new",
    srcs = ["test_new.py"],
    deps = [
        "//sematic/cli:new",
        "//sematic/cli:examples_utils",
    ],
    pip_deps = [
        "click",
    ]
)