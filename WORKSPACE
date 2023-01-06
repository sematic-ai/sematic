workspace(name = "sematic")

load("@bazel_tools//tools/build_defs/repo:git.bzl", "git_repository")
load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

## NEEDED FOR M1 MAC SUPPORT
# The docker rules do not use go in a way that supports M1s by default, so
# this updates the go used.

http_archive(
    name = "platforms",
    sha256 = "379113459b0feaf6bfbb584a91874c065078aa673222846ac765f86661c27407",
    urls = [
        "https://mirror.bazel.build/github.com/bazelbuild/platforms/releases/download/0.0.5/platforms-0.0.5.tar.gz",
        "https://github.com/bazelbuild/platforms/releases/download/0.0.5/platforms-0.0.5.tar.gz",
    ],
)

http_archive(
    name = "io_bazel_rules_go",
    sha256 = "16e9fca53ed6bd4ff4ad76facc9b7b651a89db1689a2877d6fd7b82aa824e366",
    urls = [
        "https://mirror.bazel.build/github.com/bazelbuild/rules_go/releases/download/v0.34.0/rules_go-v0.34.0.zip",
        "https://github.com/bazelbuild/rules_go/releases/download/v0.34.0/rules_go-v0.34.0.zip",
    ],
)

http_archive(
    name = "bazel_gazelle",
    sha256 = "501deb3d5695ab658e82f6f6f549ba681ea3ca2a5fb7911154b5aa45596183fa",
    urls = [
        "https://mirror.bazel.build/github.com/bazelbuild/bazel-gazelle/releases/download/v0.26.0/bazel-gazelle-v0.26.0.tar.gz",
        "https://github.com/bazelbuild/bazel-gazelle/releases/download/v0.26.0/bazel-gazelle-v0.26.0.tar.gz",
    ],
)

load("@bazel_gazelle//:deps.bzl", "gazelle_dependencies")
load("@io_bazel_rules_go//go:deps.bzl", "go_register_toolchains", "go_rules_dependencies")

go_rules_dependencies()

go_register_toolchains(version = "1.18.4")

gazelle_dependencies()

## PYTHON RULES

### Standard python rules
http_archive(
    name = "rules_python",
    sha256 = "497ca47374f48c8b067d786b512ac10a276211810f4a580178ee9b9ad139323a",
    strip_prefix = "rules_python-0.16.1",
    url = "https://github.com/bazelbuild/rules_python/archive/refs/tags/0.16.1.tar.gz",
)

# Canonical toolchain
# This fails to build wheels on M1 Macs so we use a custom toolchain

load("@rules_python//python:repositories.bzl", "python_register_toolchains")

python_register_toolchains(
    name = "python3_8",
    python_version = "3.8",
    # Setting this to False makes the python3_8 targets, platforms, etc.
    # available to bazel but SKIPS the final part where it tells bazel
    # "this is the interpreter I want you to always use." We need to skip
    # that so we can give bazel our stub interpreter instead. See stub.py.tpl
    # for an explanation.
    register_toolchains = False,
)

python_register_toolchains(
    name = "python3_9",
    python_version = "3.9",
    # See above comment about why this is False.
    register_toolchains = False,
)

# Used to register a default toolchain in /WORKSPACE.bazel,
# this is ultimately what makes it so bazel sees our stub
# interpreter as the thing to use for python things.
register_toolchains(
    "//:py_stub_toolchain"
)

# Hermetic python from https://thethoughtfulkoala.com/posts/2020/05/16/bazel-hermetic-python.html

# Special logic for building python interpreter with OpenSSL from homebrew.
# See https://devguide.python.org/setup/#macos-and-os-x
# For xz linking
# See https://qiita.com/ShotaMiyazaki94/items/d868855b379d797d605f

# <add python version>: This section will need to be updated when a python version is added
load("@python3_8//:defs.bzl", interpreter38="interpreter")
load("@python3_9//:defs.bzl", interpreter39="interpreter")
load("@rules_python//python:pip.bzl", "pip_parse")

pip_parse(
    name = "pip_dependencies38",
    python_interpreter_target = interpreter38,
    requirements_lock = "//requirements:requirements38.txt",
)

pip_parse(
    name = "pip_dependencies39",
    python_interpreter_target = interpreter39,
    requirements_lock = "//requirements:requirements39.txt",
)

load("@pip_dependencies38//:requirements.bzl", install_deps38="install_deps")
load("@pip_dependencies39//:requirements.bzl", install_deps39="install_deps")

# Actually does the 3rd party dep installs for each of our
# hermetic interpreters to use.
install_deps38()
install_deps39()

# Used to enable multiple interpreters for tests
# approach from https://blog.aspect.dev/many-python-versions-one-bazel-build
http_archive(
    name = "aspect_bazel_lib",
    sha256 = "33332c0cd7b5238b5162b5177da7f45a05641f342cf6d04080b9775233900acf",
    strip_prefix = "bazel-lib-1.10.0",
    url = "https://github.com/aspect-build/bazel-lib/archive/refs/tags/v1.10.0.tar.gz",
)

## DOCKER RULES

http_archive(
    name = "io_bazel_rules_docker",
    sha256 = "b1e80761a8a8243d03ebca8845e9cc1ba6c82ce7c5179ce2b295cd36f7e394bf",
    urls = ["https://github.com/bazelbuild/rules_docker/releases/download/v0.25.0/rules_docker-v0.25.0.tar.gz"],
)

load(
    "@io_bazel_rules_docker//repositories:repositories.bzl",
    container_repositories = "repositories",
)

container_repositories()

load(
    "@io_bazel_rules_docker//python3:image.bzl",
    _py_image_repos = "repositories",
)

_py_image_repos()

load("@sematic//bazel:pipeline.bzl", "base_images")

base_images()
