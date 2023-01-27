sematic_py_lib(
    name = "cluster",
    srcs = ["cluster.py"],
    deps = [
        "//sematic/plugins:abstract_external_resource",
        "//sematic:abstract_plugin",
        "//sematic/scheduling:kubernetes",
        "//sematic/config:settings",
        "//sematic/plugins:abstract_kuberay_wrapper",
        "//sematic/plugins/kuberay_wrapper:standard",
        "//sematic/db:queries",
        "//sematic/utils:exceptions",
        "//sematic/config:server_settings",
    ],
    pip_deps=[
        "kubernetes",
        "ray",
    ],
)

sematic_py_lib(
    name = "spark_cluster",
    srcs = ["spark_cluster.py"],
    deps = [
        ":cluster",
    ],
    pip_deps=[
        "raydp",
        "pyspark",
    ],
)