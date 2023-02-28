load("@rules_python//python:defs.bzl", "py_runtime_pair")
load("@//tools:stamp.bzl", "stamp_build_setting")
load("@aspect_bazel_lib//lib:expand_make_vars.bzl", "expand_template")

# <default py version change>: If the default version of python changes for Sematic, this
# will need updating
load("@pip_dependencies3_8//:requirements.bzl", entry_point3_8="entry_point")
load("@python3_8//:defs.bzl", interpreter3_8="interpreter")


exports_files(["README.rst"])
exports_files(["docs/changelog.md"])
exports_files(["helm/sematic-server/Chart.yaml"])

stamp_build_setting(name = "stamp")

alias(
    name = "python_coverage_tools",
    actual = entry_point3_8("coverage"),  # <default py version change>
    visibility = ["//visibility:public"],
)

# The stuff going on here is fairly complicated. It's based on the
# approach from https://blog.aspect.dev/many-python-versions-one-bazel-build
# I've updated the stub.py.tpl to include a summarizing explanation.
expand_template(
    name = "interpreter_stub",
    out = "stub.py",
    data = [
        # Reference to the binary used to run the stub.py script that
        # launches the "real" interpreter
        interpreter3_8,  # <default py version change>
    ],
    is_executable = True,
    substitutions = {
        # Template the path to the default interpreter.
        # Can't be hardcoded in stub.py because we want it to point at
        # the hermetic default interpreter, and the hermetic default
        # interpreter's path is determined by bazel.
        "%DEFAULT_PYTHON_INTERPRETER_PATH%": "$(execpath {})".format(interpreter3_8),
    },
    template = "//:stub.py.tpl",
    visibility = ["//visibility:public"],
)

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
        interpreter3_8,  # <default py version change>
        # Need the runfiles helper for when looking up the files needed for other Python versions defined
        "@bazel_tools//tools/python/runfiles",
    ],
    # We treat stub.py as if it was a python interpreter. It is executable like a "real" interpreter,
    # but what it does is select an interpreter based on the value of the WHICH_PYTHON env var, and use
    # that to actually execute things. WHICH_PYTHON is set for all python binaries thanks to overrides
    # we have set up in sematic_rules.bzl . The interpreters WHICH_PYTHON is made to point at are
    # hermetic ones.
    interpreter = "//:stub.py",
    python_version = "PY3",
    visibility = ["//visibility:public"],
)
