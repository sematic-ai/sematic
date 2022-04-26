load("@rules_python//python:packaging.bzl", "py_wheel")

glow_py_lib(
    name = "init",
    srcs = ["__init__.py"],
    visibility = ["//visibility:public"],
    deps = [
        ":calculator",
        ":resolver",
        "//glow/resolvers:local_resolver"
    ]
)

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

py_wheel(
    name = "glow_wheel",
    visibility = ["//visibility:public"],
    distribution = "glow",
    python_tag = "py3",
    version = "0.0.1",
    author = "Sematic AI",
    author_email = "emmanuel@sematic.ai",
    classifiers = [
        "Development Status :: 1 - Planning",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Visualization",
        "Typing :: Typed",
    ],
    deps = [
        "//glow:init",
        "//glow/types:init",
    ],
)
