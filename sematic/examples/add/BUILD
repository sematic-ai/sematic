load("//bazel:pipeline.bzl", "sematic_pipeline")

sematic_example(
    name = "add",
)

sematic_pipeline(
    name = "__main__",
    dev = True,
    registry = "558717131297.dkr.ecr.us-west-2.amazonaws.com",
    repository = "sematic-dev",
    bases = {
        "cuda": "@sematic-worker-cuda//image",
        "slim": "@python_39//image"
    },
    deps = [
        ":add_lib",
    ],
)
