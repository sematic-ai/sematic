pytest_test(
    name = "test_main",
    srcs = ["test_main.py"],
    pip_deps = [
        "click",
    ],
    deps = [
        "//sematic/cli:main_lib",
        "//sematic/cli:process_utils",
        "//sematic/config:config",
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

pytest_test(
    name = "test_logs",
    srcs = ["test_logs.py"],
    pip_deps = [
        "click",
    ],
    deps = [
        "//sematic/cli:logs",
        "//sematic/db:queries",
        "//sematic/db/tests:fixtures",
        "//sematic/tests:fixtures",
    ],
)

pytest_test(
    name = "test_settings",
    srcs = ["test_settings.py"],
    pip_deps = [
        "click",
    ],
    deps = [
        "//sematic/cli:settings",
        "//sematic/config:user_settings",
        "//sematic/plugins/storage:s3_storage",
    ],
)