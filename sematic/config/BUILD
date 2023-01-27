sematic_py_lib(
    name = "init",
    srcs = ["__init__.py"],
    deps = [
        "//sematic/utils:exceptions",
    ],
)

sematic_py_lib(
    name = "config_dir",
    srcs = ["config_dir.py"],
    deps = [],
)

sematic_py_lib(
    name = "settings",
    srcs = ["settings.py"],
    pip_deps = [
        "pyyaml",
    ],
    deps = [
        ":config_dir",
        "//sematic:abstract_plugin",
        "//sematic:versions",
    ],
)

sematic_py_lib(
    name = "server_settings",
    srcs = ["server_settings.py"],
    deps = [
        ":settings",
        "//sematic:abstract_plugin",
    ],
)

sematic_py_lib(
    name = "user_settings",
    srcs = ["user_settings.py"],
    deps = [
        ":settings",
    ],
)

sematic_py_lib(
    name = "config",
    srcs = ["config.py"],
    deps = [
        ":config_dir",
        ":server_settings",
        ":settings",
        ":user_settings",
        "//sematic:versions",
    ],
)
