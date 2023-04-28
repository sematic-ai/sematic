sematic_py_lib(
    name = "algorithms",
    srcs = ["algorithms.py"],
    deps = [],
)

sematic_py_lib(
    name = "exceptions",
    srcs = ["exceptions.py"],
    deps = [
        "//sematic:abstract_calculator",
    ],
)

sematic_py_lib(
    name = "git",
    srcs = ["git.py"],
    pip_deps = [
        "git-python",
    ],
    deps = [
        "//sematic/db/models:git_info",
    ],
)

sematic_py_lib(
    name = "hashing",
    srcs = ["hashing.py"],
    deps = [
        ":json",
    ],
)

sematic_py_lib(
    name = "json",
    srcs = ["json.py"],
    deps = [],
)

sematic_py_lib(
    name = "memoized_property",
    srcs = ["memoized_property.py"],
    deps = [],
)

sematic_py_lib(
    name = "retry",
    srcs = ["retry.py"],
    deps = [],
)

sematic_py_lib(
    name = "signals",
    srcs = ["signals.py"],
    deps = [],
)

sematic_py_lib(
    name = "stdout",
    srcs = ["stdout.py"],
    deps = [],
)

sematic_py_lib(
    name = "timeout",
    srcs = ["timeout.py"],
    deps = [
        "//sematic/utils:exceptions",
    ],
)

sematic_py_lib(
    name = "db",
    srcs = ["db.py"],
    pip_deps = [
        "sqlalchemy",
    ],
    deps = [],
)
