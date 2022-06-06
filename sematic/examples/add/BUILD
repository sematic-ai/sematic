sematic_py_lib(
    name = "calculators",
    srcs = ["calculators.py"],
    deps = [
        "//sematic:init",
    ]
)

sematic_py_lib(
    name = "main_lib",
    srcs = ["main.py"],
    deps = [
        ":calculators",
        "//sematic:init",
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
