workspace(name = "glow_ws")

load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

"""
# This will be needed when we set up a hermetic python env

http_archive(
    name = "python3",
    build_file = "@glow_ws//tools/third_party:python3.BUILD",
    url = "https://anaconda.org/conda-forge/python/3.7.3/download/linux-64/python-3.7.3-h357f687_2.tar.bz2",
)

http_archive(
    name = "python3_pip",
    build_file = "@glow_ws//tools/third_party:python3_pip.BUILD",
    url = "https://anaconda.org/conda-forge/pip/22.0.4/download/noarch/pip-22.0.4-pyhd8ed1ab_0.tar.bz2",
)

http_archive(
    name = "python3_setuptools",
    build_file = "@glow_ws//tools/third_party:python3_setuptools.BUILD",
    url = "https://anaconda.org/anaconda/setuptools/61.2.0/download/linux-64/setuptools-61.2.0-py37h06a4308_0.tar.bz2",
)

http_archive(
    name = "python3_wheel",
    build_file = "@glow_ws//tools/third_party:python3_wheels.BUILD",
    url = "https://anaconda.org/anaconda/wheel/0.37.1/download/noarch/wheel-0.37.1-pyhd3eb1b0_0.tar.bz2",
)
"""

http_archive(
    name = "rules_python",
    sha256 = "9fcf91dbcc31fde6d1edb15f117246d912c33c36f44cf681976bd886538deba6",
    strip_prefix = "rules_python-0.8.0",
    url = "https://github.com/bazelbuild/rules_python/archive/refs/tags/0.8.0.tar.gz",
)


load("@rules_python//python:repositories.bzl", "python_register_toolchains")

python_register_toolchains(
    name = "python3_9",
    # Available versions are listed in @rules_python//python:versions.bzl.
    # We recommend using the same version your team is already standardized on.
    python_version = "3.9",
)

load("@python3_9//:defs.bzl", "interpreter")

load("@rules_python//python:pip.bzl", "pip_parse")

pip_parse(
    name = "glow",
    requirements_lock = "//requirements:requirements.txt",
    python_interpreter_target = interpreter,
)

load("@glow//:requirements.bzl", "install_deps")
install_deps()
