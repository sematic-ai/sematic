load("//bazel:pipeline.bzl", "sematic_pipeline")

sematic_example(
    name = "testing_pipeline",
)

sematic_pipeline(
    name = "__main__",
    dev = True,
    registry = "558717131297.dkr.ecr.us-west-2.amazonaws.com",
    repository = "sematic-dev",
    deps = [
        ":testing_pipeline_lib",
        requirement("debugpy"),
    ],
)
