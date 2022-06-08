load("@rules_python//python:defs.bzl", "py_runtime_pair")

py_runtime(
    name = "python3_runtime",
    files = ["@python_interpreter//:files"],
    interpreter = "@python_interpreter//:python_bin",
    python_version = "PY3",
    visibility = ["//visibility:public"],
)

py_runtime_pair(
    name = "sematic_py_runtime_pair",
    py2_runtime = None,
    py3_runtime = ":python3_runtime",
)

toolchain(
    name = "sematic_py_toolchain",
    toolchain = ":sematic_py_runtime_pair",
    toolchain_type = "@bazel_tools//tools/python:toolchain_type",
)

exports_files(["README.rst"])
