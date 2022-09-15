pytest_test(
    name = "test_kubernetes",
    srcs = ["test_kubernetes.py"],
    deps = [
        "//sematic/scheduling:kubernetes",
        "//sematic/resolvers:resource_requirements",
        "//sematic/tests:fixtures",
    ],
    pip_deps = [
        "kubernetes",
    ]
)