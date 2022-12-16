sematic_py_lib(
    name = "init",
    srcs = ["__init__.py"],
    pip_deps = [],
    deps = [
        ":caching",
        "//sematic:abstract_future",
        "//sematic/types:serialization",
        "//sematic/utils:hashing",
    ],
)

sematic_py_lib(
    name = "caching",
    srcs = ["caching.py"],
    pip_deps = [],
    deps = [
        "//sematic:abstract_future",
        "//sematic/types:serialization",
        "//sematic/utils:hashing",
    ],
)

sematic_py_lib(
    name = "git",
    srcs = ["git.py"],
    pip_deps = [],
    deps = [
        "//sematic:abstract_future",
        "//sematic/utils:git",
    ],
)
