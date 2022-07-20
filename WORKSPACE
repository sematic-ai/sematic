workspace(name = "sematic_ws")

load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

## PYTHON RULES

http_archive(
    name = "rules_python",
    sha256 = "9fcf91dbcc31fde6d1edb15f117246d912c33c36f44cf681976bd886538deba6",
    strip_prefix = "rules_python-0.8.0",
    url = "https://github.com/bazelbuild/rules_python/archive/refs/tags/0.8.0.tar.gz",
)

## Canonical host toolchain

load("@rules_python//python:repositories.bzl", "python_register_toolchains")

python_register_toolchains(
    name = "python3_9",
    python_version = "3.9",
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
load("@python3_9//:defs.bzl", "interpreter")
load("@rules_python//python:pip.bzl", "pip_parse")

pip_parse(
    name = "pip_dependencies",
    # Cannonical
    python_interpreter_target = interpreter,
    # Hermetic
    #python_interpreter_target = "@python_interpreter//:python_bin",
    requirements_lock = "//requirements:requirements.txt",
    # pip_data_exclude = ["*.dist-info/*"],
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

load("@io_bazel_rules_docker//container:pull.bzl", "container_pull")

container_pull(
    name = "python_39",
    digest = "sha256:4169ae884e9e7d9bd6d005d82fc8682e7d34b7b962ee7c2ad59c42480657cb1d",
    registry = "index.docker.io",
    repository = "python",
    # tag field is ignored since digest is set
    tag = "3.9-slim-bullseye",
)

container_pull(
    name = "sematic-worker-base",
    digest = "sha256:d0c0e15f4f20dc60e844523a012c9cc927acbd4c5187b943a4a4a90b0ed70eee",
    registry = "index.docker.io",
    repository = "sematicai/sematic-worker-base",
    tag = "latest",
)

container_pull(
    name = "sematic-worker-cuda",
    digest = "sha256:6cbedeffdbf8ef0e5182819b4ae05a12972f61a4cd862fe41e4b3aaca01888da",
    registry = "index.docker.io",
    repository = "sematicai/sematic-worker-base",
    tag = "cuda",
)
