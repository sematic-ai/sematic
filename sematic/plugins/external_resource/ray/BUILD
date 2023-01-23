sematic_py_lib(
    name = "cluster",
    srcs = ["cluster.py"],
    deps = [
        "//sematic:api_client",
        "//sematic:future_context",
        "//sematic/plugins:abstract_external_resource",
        "//sematic:abstract_plugin",
        "//sematic/scheduling:kubernetes",
        "//sematic/config:settings",
        "//sematic/plugins:abstract_kuberay_wrapper",
        "//sematic/plugins/kuberay_wrapper:standard",
        "//sematic/utils:exceptions",
        "//sematic/config:server_settings",
    ],
    pip_deps=[
        "kubernetes",
    ],
)
