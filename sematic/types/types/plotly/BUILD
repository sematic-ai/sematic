sematic_py_lib(
    name = "init",
    srcs = ["__init__.py"],
    deps = [
        ":figure",
    ]
)

sematic_py_lib(
    name = "figure",
    srcs = ["figure.py"],
    deps = [
        # DO NOT ADD plotly HERE
        "//sematic/types:registry",
    ]
)