pytest_test(
    name = "test_runs",
    srcs = ["test_runs.py"],
    deps = [
        "//sematic/api/tests:fixtures",
        "//sematic/db/tests:fixtures",
        "//sematic/db:queries",
        requirement("flask"),
    ]
)

pytest_test(
    name = "test_comments",
    srcs = ["test_comments.py"],
    deps = [
        "//sematic/api/tests:fixtures",
        "//sematic/db/tests:fixtures",
        "//sematic/db:queries",
        "//sematic/db/models:run",
        "//sematic/db/models:comment",
        requirement("flask"),
        requirement("sqlalchemy"),
    ]
)