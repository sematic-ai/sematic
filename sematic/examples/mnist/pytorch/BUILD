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

pip_deps = [
    "torch",
    "torchvision",
    "torchmetrics",
    "plotly",
    "pandas",
    "scikit-learn",
]

py_library(
    name = "mnist_train_lib",
    srcs = glob([
        "*.py",
        "**/*.py",
    ]),
    deps = [
        "//sematic:init",
    ] + [
        requirement(pip_dep) for pip_dep in pip_deps
    ],
)

sematic_py_lib(
    name = "mnist_train_sematic_lib",
    srcs = glob([
        "*.py",
        "**/*.py",
    ]),
    deps = [
        "//sematic:init",
    ],
    pip_deps = pip_deps,
)

sematic_pipeline(
    name = "mnist_train",
    dev = True,
    base = "@sematic-worker-cuda//image",
    registry = "558717131297.dkr.ecr.us-west-2.amazonaws.com",
    repository = "sematic-dev",
    deps = [
        ":mnist_train_lib",
    ],
)

py_library(
    name = "mnist_learning_rates_lib",
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
    name = "mnist_learning_rates",
    dev = True,
    base = "@sematic-worker-cuda//image",
    registry = "558717131297.dkr.ecr.us-west-2.amazonaws.com",
    repository = "sematic-dev",
    deps = [
        ":mnist_learning_rates_lib",
    ],
)