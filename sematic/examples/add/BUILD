load("//bazel:pipeline.bzl", "sematic_pipeline")

sematic_example(
    name = "add",
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
