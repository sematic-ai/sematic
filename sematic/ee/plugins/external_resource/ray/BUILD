sematic_py_lib(
    name = "cluster",
    srcs = ["cluster.py"],
    pip_deps = [
        "kubernetes",
        "ray",
    ],
    deps = [
        "//sematic:abstract_plugin",
        "//sematic/config:server_settings",
        "//sematic/config:settings",
        "//sematic/db:queries",
        "//sematic/ee/plugins:tracked_plugin_mixin",
        "//sematic/plugins:abstract_external_resource",
        "//sematic/plugins:abstract_kuberay_wrapper",
        "//sematic/plugins/kuberay_wrapper:standard",
        "//sematic/scheduling:kubernetes",
        "//sematic/utils:exceptions",
        "//sematic/utils:retry",
    ],
)
