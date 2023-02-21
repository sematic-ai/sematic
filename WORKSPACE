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

python_register_toolchains(
    name = "python3_10",
    python_version = "3.10",
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
load("@python3_8//:defs.bzl", interpreter3_8="interpreter")
load("@python3_9//:defs.bzl", interpreter3_9="interpreter")
load("@python3_10//:defs.bzl", interpreter3_10="interpreter")
load("@rules_python//python:pip.bzl", "pip_parse")

# Accessing our platform from within a WORKSPACE is a sin against
# the bazel gods (which is why it is done in this roundabout way)
# ...but the python ecosystem in bazel is so hacked
# together in general that I'm not sure there's another way to get
# platform-dependent requirements.
_ON_OSX = "apple" in interpreter3_8
_REQS_SUFFIX = "_osx" if _ON_OSX else "_linux"


pip_parse(
    name = "pip_dependencies3_8",
    python_interpreter_target = interpreter3_8,
    requirements_lock = "//requirements:requirements3_8{}.txt".format(_REQS_SUFFIX),
)

pip_parse(
    name = "pip_dependencies3_9",
    python_interpreter_target = interpreter3_9,
    requirements_lock = "//requirements:requirements3_9{}.txt".format(_REQS_SUFFIX),
)

pip_parse(
    name = "pip_dependencies3_10",
    python_interpreter_target = interpreter3_10,
    requirements_lock = "//requirements:requirements3_10{}.txt".format(_REQS_SUFFIX),
)

load("@pip_dependencies3_8//:requirements.bzl", install_deps3_8="install_deps")
load("@pip_dependencies3_9//:requirements.bzl", install_deps3_9="install_deps")
load("@pip_dependencies3_10//:requirements.bzl", install_deps3_10="install_deps")

# Actually does the 3rd party dep installs for each of our
# hermetic interpreters to use.
install_deps3_8()
install_deps3_9()
install_deps3_10()

# Used to enable multiple interpreters for tests
# approach from https://blog.aspect.dev/many-python-versions-one-bazel-build
http_archive(
    name = "aspect_bazel_lib",
    sha256 = "79623d656aa23ad3fd4692ab99786c613cd36e49f5566469ed97bc9b4c655f03",
    strip_prefix = "bazel-lib-1.23.3",
    url = "https://github.com/aspect-build/bazel-lib/archive/refs/tags/v1.23.3.tar.gz",
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
