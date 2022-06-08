load("@rules_python//python:packaging.bzl", "py_wheel", "py_package")

sematic_py_lib(
    name = "init",
    srcs = ["__init__.py"],
    deps = [
        ":calculator",
        ":resolver",
        "//sematic/resolvers:offline_resolver",
        "//sematic/types:init",
        "//sematic/types:casting",
    ]
)

sematic_py_lib(
    name = "config",
    srcs = ["config.py"],
    deps = []
)

sematic_py_lib(
    name = "api_client",
    srcs = ["api_client.py"],
    deps = [
        ":config",
        requirement("requests")
    ]
)

sematic_py_lib(
    name = "abstract_calculator",
    srcs = ["abstract_calculator.py"],
    deps = []
)

sematic_py_lib(
    name = "abstract_future",
    srcs = ["abstract_future.py"],
    deps = [
        ":abstract_calculator",
    ]
)

sematic_py_lib(
    name = "calculator",
    srcs = ["calculator.py"],
    deps = [
        ":abstract_calculator",
        ":future",
        "//sematic/types:casting",
        "//sematic/types:init",
        "//sematic/types:type",
        "//sematic/utils:memoized_property",
    ]
)

sematic_py_lib(
    name = "future",
    srcs = ["future.py"],
    deps = [
        ":abstract_calculator",
        ":abstract_future",
        ":resolver",
    ]
)

sematic_py_lib(
    name = "resolver",
    srcs = ["resolver.py"],
    deps = [
        ":abstract_future",
    ]
)

py_package(
    name = "wheel_package",
    deps = [
        "//sematic:init",
        "//sematic/cli:main_lib",
    ]
)


py_wheel(
    name = "sematic_wheel",
    visibility = ["//visibility:public"],
    distribution = "sematic",
    python_tag = "py3",
    platform = "any",
    version = "0.0.2.alpha.{BUILD_TIMESTAMP}",
    description_file = "//:README.rst",
    author = "Sematic AI, Inc.",
    author_email = "emmanuel@sematic.ai",
    homepage = "https://sematic.ai",
    classifiers = [
        "Development Status :: 1 - Planning",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Visualization",
        "Typing :: Typed",
    ],
    entry_points={"console_scripts": ["sematic = sematic.cli.main:main"]},
    deps = [
        ":wheel_package",
    ],
)
