load("@rules_python//python/pip_install:requirements.bzl", compile_pip_requirements="compile_pip_requirements")

# <add python version>: This section will need to be updated when a python version is added
load("@python3_8//:defs.bzl", py_binary3_8="py_binary")
load("@python3_9//:defs.bzl", py_binary3_9="py_binary")
load("@python3_10//:defs.bzl", py_binary3_10="py_binary")

compile_pip_requirements(
    name = "requirements3_8_osx",
    py_binary=py_binary3_8,
    size = "large",
    timeout = "long",
    extra_args = [
        "--allow-unsafe",
    ],
    requirements_in = "//requirements:requirements.in",
    requirements_txt = "//requirements:requirements3_8_osx.txt",
)

compile_pip_requirements(
    name = "requirements3_9_osx",
    py_binary=py_binary3_9,
    size = "large",
    timeout = "long",
    extra_args = [
        "--allow-unsafe",
    ],
    requirements_in = "//requirements:requirements.in",
    requirements_txt = "//requirements:requirements3_9_osx.txt",
)

compile_pip_requirements(
    name = "requirements3_10_osx",
    py_binary=py_binary3_10,
    size = "large",
    timeout = "long",
    extra_args = [
        "--allow-unsafe",
    ],
    requirements_in = "//requirements:requirements.in",
    requirements_txt = "//requirements:requirements3_10_osx.txt",
)


compile_pip_requirements(
    name = "requirements3_8_linux",
    py_binary=py_binary3_8,
    size = "large",
    timeout = "long",
    extra_args = [
        "--allow-unsafe",
    ],
    requirements_in = "//requirements:requirements.in",
    requirements_txt = "//requirements:requirements3_8_linux.txt",
)

compile_pip_requirements(
    name = "requirements3_9_linux",
    py_binary=py_binary3_9,
    size = "large",
    timeout = "long",
    extra_args = [
        "--allow-unsafe",
    ],
    requirements_in = "//requirements:requirements.in",
    requirements_txt = "//requirements:requirements3_9_linux.txt",
)

compile_pip_requirements(
    name = "requirements3_10_linux",
    py_binary=py_binary3_10,
    size = "large",
    timeout = "long",
    extra_args = [
        "--allow-unsafe",
    ],
    requirements_in = "//requirements:requirements.in",
    requirements_txt = "//requirements:requirements3_10_linux.txt",
)