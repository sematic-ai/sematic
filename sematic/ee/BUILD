sematic_py_lib(
    name = "ray",
    srcs = ["ray.py"],
    deps = [
        "//sematic/ee/plugins/external_resource/ray:checkpoint",
        "//sematic/ee/plugins/external_resource/ray:cluster",
        "//sematic/plugins:abstract_kuberay_wrapper",
    ],
)

sematic_py_lib(
    name = "metrics",
    srcs = ["metrics.py"],
    deps = [
        "//sematic:api_client",
        "//sematic:future_context",
        "//sematic/metrics:metric_point",
    ],
)
