load("@rules_python//python:repositories.bzl", "python_register_toolchains")
load(
    "@io_bazel_rules_docker//repositories:repositories.bzl",
    "repositories",
)

def toolchain():
    python_register_toolchains(
        name = "python3_9",
        python_version = "3.9",
    )

    repositories()
