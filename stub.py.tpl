#! /usr/bin/env python3
# This file is used to enable bazel to work with multiple python versions
# within the context of one workspace. It is based on an approach from:
# https://blog.aspect.dev/many-python-versions-one-bazel-build
# The code itself, referenced in that blog, comes from this gist:
# https://gist.github.com/mattem/57019db2e4e37e495879e734eaaa843a
# Here is a high-level summary of how this 'multiple python' setup works:
# - We register our python toolchain with bazel to point at a custom interpreter
# - That custom interpreter is actually generated from this file (note that due
# to the hash-bang, this file can be executed by the shell directly, like an
# intepreter)
# - It is *generated* from this file because we need to update
# DEFAULT_PYTHON_INTERPRETER_PATH from within a bazel build, to point it at
# a hermetic python interpreter (whose path is only known from within a bazel
# build).
# - This file itself will be executed by the host system's python, NOT a hermetic
# python.
# - What this file DOES, however, is forward execution to another python interpreter
# which IS hermetic.
# - The interpreter forwarded to is determined either by DEFAULT_PYTHON_INTERPRETER_PATH
# (default case) OR by the WHICH_PYTHON env var
# - The WHICH_PYTHON env var is overridden to point at an appropriate hermetic interpreter
# based on the bazel target that was invoked. We define overrides for it in sematic_rules.bzl
# - The available hermetic interpreters are set up, including 3rd party deps, in the WORKSPACE
import os
import sys

# Other third party deps will not be available here. Bazel also doesn't need to
# be installed for the system interpreter for this to work. My GUESS is that
# when bazel invokes an interpreter, it modifies the python path to make this
# available.
from bazel_tools.tools.python.runfiles import runfiles

DEFAULT_PYTHON_FLAGS = ["-B", "-s"]
ARGV = sys.argv[1:]

EXTERNAL = "external/"
DEFAULT_PYTHON_INTERPRETER_PATH = "%DEFAULT_PYTHON_INTERPRETER_PATH%"[len(EXTERNAL):]


def get_python_from_env():
    python = os.environ.get("WHICH_PYTHON")

    runfiles_helper = runfiles.Create()

    # Check if this path exists, if it does it's likely a direct path to the interpreter binary
    if python is not None and not os.path.isfile(python):
        # Doesn't exist, see if we can look up the path via the runfiles helper.
        try:
            python = runfiles_helper.Rlocation(python[len(EXTERNAL):])
        except Exception as e:
            print(f"'WHICH_PYTHON' ({python}) is not a file, and lookup failed via runfiles with error: ", e, file=sys.stderr, flush=True)
            # It's not a file, and we couldn't look it up in the runfiles helper,
            # attempt to fallback to the default if we can
            pass

    if python == None:
        if "BAZEL_NO_FALLBACK_TO_DEFAULT_PYTHON" in os.environ:
            print(
                "Expected 'WHICH_PYTHON' to be set to a python interpreter path, but got None",
                file=sys.stderr,
                flush=True,
            )
            sys.exit(1)

        try:
            runfiles_interpreter_path = runfiles_helper.Rlocation(DEFAULT_PYTHON_INTERPRETER_PATH)
        except Exception as e:
            print(
                "Failed to find fallback Python version in the runfiles of the target, looked for path in %s" % DEFAULT_PYTHON_INTERPRETER_PATH,
                e,
                file=sys.stderr,
                flush=True,
            )
            sys.exit(1)

        python = runfiles_interpreter_path

    return python


def main():
    python = get_python_from_env()

    args = [python] + DEFAULT_PYTHON_FLAGS + ARGV

    try:
        os.execv(python, args)
    except Exception as e:
        print(e, file=sys.stderr, flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
