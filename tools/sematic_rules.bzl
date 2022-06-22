"""
pytest_test rule
"""

load(
    "@rules_python//python:defs.bzl",
    "py_test",
    "py_library",
    "py_binary",
)

load("@sematic//:requirements.bzl", "requirement")

def pytest_test(name, srcs, deps = [], args = [], **kwargs):

    py_test(
        name = name,
        srcs = ["//tools:pytest_runner"] + srcs,
        main = "tools/pytest_runner.py",
        deps = deps,
        args = args + ["$(location :%s)" % x for x in srcs],
        **kwargs
    )


def sematic_py_lib(name, srcs, deps, visibility = None, data = None):
    if visibility == None:
        visibility = ["//visibility:public"]

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


def sematic_example(name, requirements = None, data = None):
    sematic_py_lib(
        name = "{}_lib".format(name),
        srcs = native.glob(["*.py", "**/*.py"]),
        data = ["requirements.txt", "README", "AUTHORS"] + (data or []),
        deps = [
            "//sematic:init",
        ]
    )

    sematic_py_lib(
        name = "requirements",
        srcs = ["__main__.py"],
        deps = [
            requirement(req) for req in (requirements or [])
        ]
    )

    py_binary(
        name = name,
        main = "__main__.py",
        srcs = ["__main__.py"],
        deps = [
            ":{}_lib".format(name),
            ":requirements",
        ]
    )