load("@rules_python//python/pip_install:requirements.bzl", compile_pip_requirements="compile_pip_requirements")

# <add python version>: This section will need to be updated when a python version is added
load("@python3_8//:defs.bzl", py_binary38="py_binary")
load("@python3_9//:defs.bzl", py_binary39="py_binary")

compile_pip_requirements(
    name = "requirements38",
    py_binary=py_binary38,
    size = "large",
    timeout = "long",
    extra_args = [
        "--allow-unsafe",
    ],
    requirements_in = "//requirements:requirements.in",
    requirements_txt = "//requirements:requirements38.txt",
)

compile_pip_requirements(
    name = "requirements39",
    py_binary=py_binary39,
    size = "large",
    timeout = "long",
    extra_args = [
        "--allow-unsafe",
    ],
    requirements_in = "//requirements:requirements.in",
    requirements_txt = "//requirements:requirements39.txt",
)
