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
    name = "user_settings",
    srcs = ["user_settings.py"],
    pip_deps = [
        "pyyaml",
    ],
    deps = [
        ":config_dir",
    ],
)

sematic_py_lib(
    name = "config",
    srcs = ["config.py"],
    deps = [
        ":config_dir",
        ":user_settings",
    ],
)
