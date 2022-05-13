glow_py_lib(
    name = "calculators",
    srcs = ["calculators.py"],
    visibility = ["//visibility:public"],
    deps = [
        "//glow:init",
    ]
)

glow_py_lib(
    name = "main_lib",
    srcs = ["main.py"],
    visibility = ["//visibility:public"],
    deps = [
        ":calculators",
        "//glow:init",
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
