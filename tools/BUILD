package(default_visibility = ["//visibility:public"])

# Can't use things from sematic_rules here; sematic_rules
# depends on this BUILD file.
py_library(
    name = "pytest_runner",
    srcs = ["pytest_runner.py"],

    # pytest_runner does import pytest, so you might think we would want
    # a pytest dep here. However, we can't specify a third-party dep in a
    # standard py_library without specifying which interpreter has that
    # pip dep. To keep this target python-version agnostic, leave the
    # pytest dep out. The 'pytest_test' macro should add an appropriately
    # versioned pip dep to all pytest tests.
    deps = [],
)

sh_binary(
    name = "switch-settings",
    srcs = ["switch-settings.sh"],
)
