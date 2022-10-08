load("//bazel:pipeline.bzl", "sematic_pipeline")

sematic_py_lib(
    name = "pipeline",
    srcs = ["pipeline.py"],
    deps = [
        "//sematic:init",
    ],
)

sematic_pipeline(
    name = "__main__",
    dev = True,
    registry = "558717131297.dkr.ecr.us-west-2.amazonaws.com",
    repository = "sematic-dev",
    deps = [
        ":add_lib",
    ],
)
