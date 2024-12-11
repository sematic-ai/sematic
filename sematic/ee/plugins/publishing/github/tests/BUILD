pytest_test(
    name = "test_check",
    srcs = ["test_check.py"],
    py_versions = [PY3.PY3_9, PY3.PY3_10, PY3.PY3_11],
    deps = [
        "//sematic:abstract_future",
        "//sematic/db/models:git_info",
        "//sematic/db/models:resolution",
        "//sematic/db/models:run",
        "//sematic/db:queries",
        "//sematic/db/tests:fixtures",
        "//sematic/ee/plugins/publishing/github:check",
    ],
)
