load("//bazel:pipeline.bzl", "sematic_pipeline")

sematic_example(
    name = "pytorch",
    requirements = [
        "torch",
        "torchvision",
        "torchmetrics",
        "plotly",
        "pandas",
        "scikit-learn",
    ],
)

py_library(
    name = "mnist_pytorch_lib",
    srcs = glob([
        "*.py",
        "**/*.py",
    ]),
    deps = [
        "//sematic:init",
        requirement("torch"),
        requirement("torchvision"),
        requirement("torchmetrics"),
        requirement("plotly"),
        requirement("pandas"),
        requirement("scikit-learn"),
    ],
)

sematic_pipeline(
    name = "mnist_pytorch",
    registry = "558717131297.dkr.ecr.us-west-2.amazonaws.com",
    repository = "sematic-dev",
    deps = [
        ":mnist_pytorch_lib",
    ],
)
