pytest_test(
    name = "test_dataframe",
    srcs = ["test_dataframe.py"],
    data = ["cirrhosis.csv"],
    deps = [
        "//sematic/types:serialization",
        "//sematic/types:init",
        "//sematic/db/models:factories",
    ],
    pip_deps = [
        "pandas",
    ]
)