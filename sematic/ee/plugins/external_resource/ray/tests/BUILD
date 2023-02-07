pytest_test(
    name = "test_cluster",
    srcs = ["test_cluster.py"],
    pip_deps = [
        "kubernetes",
        "ray",
    ],
    deps = [
        "//sematic/ee/plugins/external_resource/ray:cluster",
        "//sematic:calculator",
        "//sematic/plugins:abstract_external_resource",
        "//sematic/tests:fixtures",
    ],
)