load("//tools:sematic_pipeline.bzl", "sematic_pipeline")

sematic_py_lib(
    name = "bazel_lib",
    srcs = glob([
        "*.py",
        "**/*.py",
    ]),
    deps = [
        "//sematic:init",
    ],
)

sematic_pipeline(
    name = "bazel",
    base = "@sematic-worker-base//image",
    registry = "558717131297.dkr.ecr.us-west-2.amazonaws.com",
    repository = "sematic-dev",
    deps = [
        ":bazel_lib",
    ],
)
