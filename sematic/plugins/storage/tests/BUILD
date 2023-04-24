pytest_test(
    name = "test_memory_storage",
    srcs = ["test_memory_storage.py"],
    pip_deps = ["flask"],
    deps = [
        "//sematic/api/tests:fixtures",
        "//sematic/db/tests:fixtures",
        "//sematic/plugins/storage:memory_storage",
    ],
)

pytest_test(
    name = "test_local_storage",
    srcs = ["test_local_storage.py"],
    pip_deps = ["flask"],
    # buildifier: leave-alone
    deps = [
        "//sematic/api/tests:fixtures",
        "//sematic/config:config",
        "//sematic/config/tests:fixtures",
        "//sematic/db/tests:fixtures",
        "//sematic/plugins/storage:local_storage",
    ],
)

pytest_test(
    name = "test_s3_storage",
    srcs = ["test_s3_storage.py"],
    pip_deps = ["flask"],
    deps = [
        "//sematic/api/tests:fixtures",
        "//sematic/db/tests:fixtures",
        "//sematic/plugins/storage:s3_storage",
    ],
)
