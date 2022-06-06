sematic_py_lib(
    name = "main_lib",
    srcs = ["main.py", "calculators.py", "train_eval.py"],
    deps = [
        "//sematic:init",
        requirement("torch"),
        requirement("torchvision"),
        requirement("torchmetrics"),
        requirement("plotly"),
        requirement("pandas"),
    ]
)

py_binary(
    name = "main",
    main = "main.py",
    srcs = ["main.py"],
    deps = [
        ":main_lib"
    ]
)
