sematic_py_lib(
    name = "figure",
    srcs = ["figure.py"],
    deps = [
        "//sematic/types:registry",
        "//sematic:config",
        # Do not add matplotlib here
    ]
)

sematic_py_lib(
    name = "init",
    srcs = ["__init__.py"],
    deps = [
        ":figure"
    ]
)
