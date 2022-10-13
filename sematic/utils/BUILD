sematic_py_lib(
    name = "exceptions",
    srcs = ["exceptions.py"],
    deps = [
        "//sematic:abstract_calculator",
    ]
)

sematic_py_lib(
    name = "memoized_property",
    srcs = ["memoized_property.py"],
    deps = []
)

sematic_py_lib(
    name = "retry",
    srcs = ["retry.py"],
    deps = []
)

sematic_py_lib(
    name = "stdout",
    srcs = ["stdout.py"],
    deps = []
)

sematic_py_lib(
    name = "git",
    srcs = ["git.py"],
    deps = [
        "//sematic/db/models:git_info",
    ],
    pip_deps = [
        "git-python",
    ],
)
