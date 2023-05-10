pytest_test(
    name = "test_checkpoint",
    srcs = ["test_checkpoint.py"],
    pip_deps = [
        "torch",
    ],
    deps = [
        "//sematic/ee/plugins/external_resource/ray:checkpoint",
    ],
)

pytest_test(
    name = "test_cluster",
    srcs = ["test_cluster.py"],
    pip_deps = [
        "kubernetes",
        "ray",
    ],
    deps = [
        "//sematic:function",
        "//sematic/ee/plugins/external_resource/ray:cluster",
        "//sematic/plugins:abstract_external_resource",
        "//sematic/tests:fixtures",
    ],
)
