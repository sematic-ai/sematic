load("@rules_python//python:defs.bzl", "py_runtime_pair")
load("@//tools:stamp.bzl", "stamp_build_setting")
load("@pip_dependencies38//:requirements.bzl", entry_point38="entry_point")
load("@aspect_bazel_lib//lib:expand_make_vars.bzl", "expand_template")
load("@rules_python//python:defs.bzl", "py_runtime_pair")
load("@python3_8//:defs.bzl", interpreter38="interpreter")

# Needed by the custom toolchain
# Can remove if we siwtch back to the canonical one
"""
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
"""

exports_files(["README.rst"])

stamp_build_setting(name = "stamp")

alias(
    name = "python_coverage_tools",
    actual = entry_point38("coverage"),
    visibility = ["//visibility:public"],
)

expand_template(
    name = "interpreter_stub",
    out = "stub.py",
    data = [
        # Reference to the binary used to run the stub.py script that
        # launches the "real" interpreter
        interpreter38,
    ],
    is_executable = True,
    substitutions = {
        # Template the path to the default interpreter
        "%DEFAULT_PYTHON_INTERPRETER_PATH%": "$(execpath {})".format(interpreter38),
    },
    template = "//:stub.py.tpl",
    visibility = ["//visibility:public"],
)
#exports_files(["stub.py"])

# Used to register a default toolchain in /WORKSPACE.bazel
toolchain(
    name = "py_stub_toolchain",
    toolchain = ":py_stub_runtime_pair",
    toolchain_type = "@bazel_tools//tools/python:toolchain_type",
)

py_runtime_pair(
    name = "py_stub_runtime_pair",
    py2_runtime = None,
    py3_runtime = ":python_stub_runtime",
)

py_runtime(
    name = "python_stub_runtime",
    files = [
        # Need the default python interpreter here as
        # a fallback version for external py_binary targets that don't set the 'WHICH_PYTHON' env var.
        interpreter38,
        # Need the runfiles helper for when looking up the files needed for other Python versions defined
        "@bazel_tools//tools/python/runfiles",
    ],
    interpreter = "//:stub.py",
    python_version = "PY3",
    visibility = ["//visibility:public"],
)
