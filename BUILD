py_library(
    name = "abstract_calculator",
    srcs = ["abstract_calculator.py"],
    visibility = ["//visibility:public"],
    deps = []
)

py_library(
    name = "abstract_future",
    srcs = ["abstract_future.py"],
    visibility = ["//visibility:public"],
    deps = []
)

py_library(
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

py_library(
    name = "future",
    srcs = ["future.py"],
    visibility = ["//visibility:public"],
    deps = [
        ":abstract_calculator",
        ":abstract_future",
        ":resolver",
    ]
)

py_library(
    name = "resolver",
    srcs = ["resolver.py"],
    visibility = ["//visibility:public"],
    deps = [
        ":abstract_future",
    ]
)