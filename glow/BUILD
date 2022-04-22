glow_py_lib(
    name = "abstract_calculator",
    srcs = ["abstract_calculator.py"],
    visibility = ["//visibility:public"],
    deps = []
)

glow_py_lib(
    name = "abstract_future",
    srcs = ["abstract_future.py"],
    visibility = ["//visibility:public"],
    deps = []
)

glow_py_lib(
    name = "calculator",
    srcs = ["calculator.py"],
    visibility = ["//visibility:public"],
    deps = [
        ":abstract_calculator",
        "//glow/types:type",
        "//glow/types/types:null",
        "//glow/utils:memoized_property",
    ]
)

glow_py_lib(
    name = "future",
    srcs = ["future.py"],
    visibility = ["//visibility:public"],
    deps = [
        ":abstract_calculator",
        ":abstract_future",
        ":resolver",
    ]
)

glow_py_lib(
    name = "resolver",
    srcs = ["resolver.py"],
    visibility = ["//visibility:public"],
    deps = [
        ":abstract_future",
    ]
)