workspace(name = "sematic")

load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

## NEEDED FOR M1 MAC SUPPORT

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

http_archive(
    name = "rules_python",
    sha256 = "9fcf91dbcc31fde6d1edb15f117246d912c33c36f44cf681976bd886538deba6",
    strip_prefix = "rules_python-0.8.0",
    url = "https://github.com/bazelbuild/rules_python/archive/refs/tags/0.8.0.tar.gz",
)

## Canonical toolchain
# This fails to build wheels on M1 Macs so we use a custom toolchain

load("@rules_python//python:repositories.bzl", "python_register_toolchains")

python_register_toolchains(
    name = "python3_8",
    python_version = "3.8",
)

# Hermetic python from https://thethoughtfulkoala.com/posts/2020/05/16/bazel-hermetic-python.html

# Special logic for building python interpreter with OpenSSL from homebrew.
# See https://devguide.python.org/setup/#macos-and-os-x
# For xz linking
# See https://qiita.com/ShotaMiyazaki94/items/d868855b379d797d605f

_py_configure = """
if [[ "$OSTYPE" == "darwin"* ]]; then
    prefix=$(brew --prefix)
    export LDFLAGS="-L$prefix/opt/xz/lib $LDFLAGS"
    export CPPFLAGS="-I$prefix/opt/xz/include $CPPFLAGS"
    export PKG_CONFIG_PATH="$prefix/opt/xz/lib/pkgconfig:$PKG_CONFIG_PATH"
    ./configure --enable-shared --prefix=$(pwd)/bazel_install --with-openssl=$(brew --prefix openssl)
else
    ./configure --prefix=$(pwd)/bazel_install
fi
"""

#http_archive(
#    name = "python_interpreter",
#    build_file_content = """
#exports_files(["python_bin"])
#filegroup(
#    name = "files",
#    srcs = glob(["bazel_install/**"], exclude = ["**/* *"]),
#    visibility = ["//visibility:public"],
#)
#""",
#    patch_cmds = [
#        "mkdir $(pwd)/bazel_install",
#        _py_configure,
#        "make",
#        "make install",
#        "ln -s bazel_install/bin/python3 python_bin",
#    ],
#    sha256 = "0a8fbfb5287ebc3a13e9baf3d54e08fa06778ffeccf6311aef821bb3a6586cc8",
#    strip_prefix = "Python-3.9.10",
#    urls = ["https://www.python.org/ftp/python/3.9.10/Python-3.9.10.tar.xz"],
#)

#register_toolchains("//:sematic_py_toolchain")

# Canonical interpreter
load("@python3_8//:defs.bzl", "interpreter")
load("@rules_python//python:pip.bzl", "pip_parse")

pip_parse(
    name = "pip_dependencies",
    # Cannonical
    python_interpreter_target = interpreter,
    # Custom
    #python_interpreter_target = "@python_interpreter//:python_bin",
    requirements_lock = "//requirements:requirements.txt",
)

load("@pip_dependencies//:requirements.bzl", "install_deps")

install_deps()

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
