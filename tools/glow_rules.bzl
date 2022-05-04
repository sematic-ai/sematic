"""
pytest_test rule
"""

load(
    "@rules_python//python:defs.bzl",
    "py_test",
    "py_library",
    "py_binary",
)

load("@glow//:requirements.bzl", "requirement")

def pytest_test(name, srcs, deps = [], args = [], **kwargs):

    py_test(
        name = name,
        srcs = ["//tools:pytest_runner"] + srcs,
        main = "tools/pytest_runner.py",
        deps = deps,
        args = args + ["$(location :%s)" % x for x in srcs],
        **kwargs
    )


def glow_py_lib(name, srcs, visibility, deps, data = None):
    py_library(
        name = name,
        srcs = srcs,
        visibility = visibility,
        deps = deps,
        data = data,
    )

    py_binary(
        name = "{0}_ipython".format(name),
        main = "//tools/jupyter:ipython.py",
        srcs = ["//tools/jupyter:ipython.py"],
        deps = [
            ":{0}".format(name),
            requirement("ipython"),
        ],
        data = data,
    )
