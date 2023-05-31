load("//bazel:pipeline.bzl", "sematic_pipeline")

sematic_example(
    name = "testing_pipeline",
    data = ["resources/sammy.png"],
    extras = [
        "//sematic/ee:ray",
    ],
    requirements = [
        "debugpy",
        "python-magic",
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
        requirement("python-magic"),
        requirement("ray"),
    ],
    deps = [
        requirement("debugpy"),
        requirement("python-magic"),
        requirement("ray"),
        ":testing_pipeline_lib",
    ],
)
