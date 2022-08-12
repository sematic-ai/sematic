#! /usr/bin/env python3

import os
import sys

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
