load("//bazel:pipeline.bzl", "sematic_pipeline")

sematic_py_lib(
    name = "pipeline",
    srcs = ["pipeline.py"],
    pip_deps = [
        "ray",
        "torch",
        "torchvision",
    ],
    py_versions = [PY3.PY3_9, PY3.PY3_8],
    deps = [
        "//sematic:function",
        "//sematic/ee:ray",
        "//sematic/examples/mnist/pytorch:mnist_train_sematic_lib",
        "//sematic/resolvers:resource_requirements",
    ],
)

sematic_pipeline(
    name = "__main__",
    base = "@sematic-worker-cuda//image",
    dev = True,
    registry = "558717131297.dkr.ecr.us-west-2.amazonaws.com",
    repository = "sematic-dev",
    deps = [
        ":pipeline",
        "//sematic:init",
        requirement("debugpy"),
    ],
)
