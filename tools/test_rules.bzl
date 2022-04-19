"""
pytest_test rule
"""

load("@rules_python//python:defs.bzl", "py_test")

def pytest_test(name, srcs, deps = [], args = [], **kwargs):

    py_test(
        name = name,
        srcs = ["//tools:pytest_runner"] + srcs,
        main = "tools/pytest_runner.py",
        deps = deps,
        args = args + ["$(location :%s)" % x for x in srcs],
        **kwargs
    )