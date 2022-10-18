sematic_py_lib(
    name = "init",
    srcs = ["__init__.py"],
    pip_deps = [],
    deps = [
        ":mock_sematic_funcs",
    ],
)

sematic_py_lib(
    name = "mock_sematic_funcs",
    srcs = ["mock_sematic_funcs.py"],
    pip_deps = [],
    deps = [
        ":local_resolver",
        "//sematic:calculator",
    ],
)