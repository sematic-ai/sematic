load("//bazel:pipeline.bzl", "sematic_pipeline")

sematic_example(
    name = "testing_pipeline",
    extras = [
        "//sematic/ee:ray",
    ],
    requirements = [
        "debugpy",
        "ray",
    ],
)

sematic_pipeline(
    name = "__main__",
    dev = True,
    registry = "558717131297.dkr.ecr.us-west-2.amazonaws.com",
    repository = "sematic-dev",
    image_layers = [
        # Include these in their own layers, since they don't change often.
        requirement("debugpy"),
        requirement("ray"),
    ],
    deps = [
        ":testing_pipeline_lib",
    ],
)
