load("//bazel:pipeline.bzl", "sematic_pipeline")


sematic_py_lib(
    name = "lib",
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
        "boto3",
        "pandas",
        "pillow",
        "plotly",
        "pytorch-lightning",
        "ray",
        "ray-lightning",
        "torch",
        "torchmetrics",
        "torchvision",
    ],
)

sematic_pipeline(
    name = "main",
    dev = True,
    base = "@sematic-worker-cuda//image",
    registry = "558717131297.dkr.ecr.us-west-2.amazonaws.com", # update this to your own registry
    repository = "sematic-dev", # update this to your own repository

    # Specifying image layers is not required, but helps
    # ensure docker image caching works well for image build & push
    image_layers = [
        requirement("torch"),
        requirement("torchvision"),
        requirement("torchmetrics"),
        requirement("ray"),
        requirement("plotly"),
    ],
    deps = [
        ":lib",
    ],
)
