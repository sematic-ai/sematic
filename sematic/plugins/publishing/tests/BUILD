pytest_test(
    name = "test_slack",
    srcs = ["test_slack.py"],
    pip_deps = ["requests"],
    deps = [
        "//sematic/config:server_settings",
        "//sematic/config/tests:fixtures",
        "//sematic/db/models:resolution",
        "//sematic/db/models:run",
        "//sematic/db/tests:fixtures",
        "//sematic/plugins/publishing:slack",
        "//sematic/tests:fixtures",
        "//sematic/tests:utils",
    ],
)
