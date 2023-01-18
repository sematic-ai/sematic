sematic_py_lib(
    name = "yolov5_lib",
    srcs = glob([
        "*.py",
        "**/*.py",
    ]),
    deps = [
        "//sematic:init",
    ],
    pip_deps = [
        "torch",
        "torchvision",
        "opencv-python",
        "pandas",
        "numpy",
        "tqdm",
        "psutil",
        "seaborn"
    ]
)

py_binary(
    name = "main",
    srcs = ["__main__.py"],
    main = "__main__.py",
    deps = [
        ":yolov5_lib",
    ],
)