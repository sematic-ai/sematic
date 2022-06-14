sematic_py_lib(
    name = "init",
    srcs = ["__init__.py"],
    deps = [
        ":dataframe",
    ]
)

sematic_py_lib(
    name = "dataframe",
    srcs = ["dataframe.py"],
    deps = [
        "//sematic/types:registry",
        # Do not add pandas here, this code path is only active if
        # pandas is already available
    ]
)