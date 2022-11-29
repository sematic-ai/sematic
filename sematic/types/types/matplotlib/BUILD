sematic_py_lib(
    name = "figure",
    srcs = ["figure.py"],
    pip_deps = [
        # Do not add matplotlib here
        "mpld3",
    ],
    deps = [
        "//sematic/types:registry",
    ],
)

sematic_py_lib(
    name = "init",
    srcs = ["__init__.py"],
    deps = [
        ":figure",
    ],
)
