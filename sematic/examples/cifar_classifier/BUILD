load("//bazel:pipeline.bzl", "sematic_pipeline")

sematic_py_lib(
    name = "cifar_classifier_lib",
    srcs = glob([
        "*.py",
        "**/*.py",
    ]),
    deps = [
        "//sematic:init",
        "//sematic/ee:ray",
    ],
    py_versions = [PY3.PY3_9, PY3.PY3_8],
    pip_deps = [
        "numpy",
        "ray",
        "torch",
        "torchvision",
        "torchmetrics",
        "pillow",
        "plotly",
    ],
)

sematic_pipeline(
    name = "main",
    dev = True,
    registry = "558717131297.dkr.ecr.us-west-2.amazonaws.com", # update this to your own registry
    repository = "sematic-dev", # update this to your own repository
    base = "@sematic-worker-cuda//image",
    image_layers = [
        requirement("torch"),
        requirement("torchvision"),
        requirement("torchmetrics"),
        requirement("ray"),
        requirement("plotly"),
    ],
    deps = [
        ":cifar_classifier_lib",
    ],
)
